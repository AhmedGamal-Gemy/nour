"""Realtime recitation check over a WebSocket.

Protocol on /ws/recite:
  1. Client sends one JSON text message to start or resume:
       {"sura": 53, "aya": 1}
     or {} to resume the last saved position (data/session_state.json).
  2. Client then streams binary frames: raw PCM16LE, mono, 16kHz. Frame
     size isn't fixed, but small (~20ms, 640 bytes) is what the pause
     detector in vad.py is tuned around.
  3. Two things can trigger a check of the buffered audio against the
     reference: a VAD-detected pause (vad.py), or - because ayahs are
     often recited back to back with no real pause between them - the
     buffer simply having grown close to how long this ayah should take
     (estimated from its phoneme count). Either way, if what's been heard
     is clearly shorter than the expected ayah, nothing is sent and
     listening continues (a VAD-triggered check also treats this as a
     breath: buffer kept as-is). Only once the heard content is close to
     the full expected length (or a VAD pause has gone on long enough
     that it's clearly not a breath anymore) does it finalize and send
     one JSON message:
       {"sura":.., "aya":.., "uthmani":.., "passed":.., "mismatches":[...]}
     On a pass it advances to the next ayah and keeps listening there.
  4. On a fail, the *next* segment is checked against two candidates: the
     same ayah (a retry) and the next one (in case the reciter moved on
     anyway without passing). Whichever matches better wins. If the next
     ayah wins, the failed one is logged as skipped (left unresolved, not
     retried) rather than silently staying stuck forever comparing new
     audio against old text.

This is chunk-based near-real-time, not live word-by-word decoding -
Quran Muaalem compares a finished clip against the reference, it does
not do streaming ASR. See CLAUDE.md section 4.

Each check runs in a thread pool executor, not inline on the event loop:
model inference takes a few seconds, and running it inline would freeze
every other connection (including health checks) for that long.
"""

import asyncio
import time

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from quran_transcript import Aya, quran_phonetizer

from backend.vad import SilenceSegmenter
from tools.session.check import MOSHAF, check_wave
from tools.session.track import load_state, log_result, save_state

# How close the heard phoneme count must be to the expected count before a
# pause is treated as the end of the ayah rather than a breath. Length, not
# content, on purpose - a tashkeel mistake doesn't change how many phonemes
# were said, only which ones, so this doesn't mask the thing we're checking for.
COMPLETENESS_RATIO = 0.85

# Calibrated from ~11 real ayahs (0.088-0.167 s/phoneme, median 0.123):
# deliberately below the median so the duration trigger starts a bit early
# rather than late - worse case is a few wasted checks, not a missed ayah.
SEC_PER_PHONEME_ESTIMATE = 0.10
# Fraction of the estimated duration before duration-based probing starts.
PROBE_START_FRACTION = 0.6
# Minimum spacing between duration-triggered checks - each one is a full
# model inference, so this caps how much CPU a long ayah burns on retries.
PROBE_INTERVAL_S = 0.5
# Multiple of the estimated duration past which a duration-triggered check
# finalizes no matter what, instead of waiting for heard_len to reach
# expected_len. Without this, a real gap in the recitation (heard_len
# staying short of expected for reasons that have nothing to do with the
# ayah being unfinished) just keeps waiting - and the only way it can ever
# reach the target length is by swallowing audio from the *next* ayah to
# make up the shortfall. Better to cut on time and show the real mismatch
# (including what's still missing) than to risk eating into what's next.
PROBE_MAX_FRACTION = 1.6


def estimate_duration_s(sura: int, aya: int) -> float:
    ref = quran_phonetizer(Aya(sura, aya).get().uthmani, MOSHAF, remove_spaces=True)
    return len(ref.phonemes) * SEC_PER_PHONEME_ESTIMATE


app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws/recite")
async def recite(ws: WebSocket):
    await ws.accept()

    start = await ws.receive_json()
    if start.get("sura") and start.get("aya"):
        sura, aya = start["sura"], start["aya"]
    else:
        state = load_state()
        if state is None:
            await ws.send_json({"error": "no saved position - send {sura, aya} to start"})
            await ws.close()
            return
        sura, aya = state["sura"], state["aya"]

    segmenter = SilenceSegmenter()
    expected_duration = estimate_duration_s(sura, aya)
    last_probe_at = time.monotonic()
    # Set after a fail: the next segment gets checked against both this
    # ayah (retry) and the one after it (maybe they moved on anyway).
    fallback_sura, fallback_aya = None, None

    try:
        while True:
            chunk = await ws.receive_bytes()
            frame = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            candidate = segmenter.push(frame)

            # No VAD pause yet, but the buffer is already close to how long
            # this ayah should take - probe it anyway. This is what lets
            # back-to-back ayahs with no real pause between them still get
            # cut at the right place.
            duration_triggered = False
            if candidate is None and not segmenter.pending:
                buf_dur = len(segmenter.buffer) / segmenter.sr
                now = time.monotonic()
                if (
                    buf_dur >= PROBE_START_FRACTION * expected_duration
                    and now - last_probe_at >= PROBE_INTERVAL_S
                ):
                    candidate = segmenter.buffer.copy()
                    duration_triggered = True
                    last_probe_at = now

            if candidate is None:
                continue

            # check_wave is synchronous and CPU-bound (model inference); run
            # it off the event loop or every other connection - including
            # health checks and this one's own pings - freezes for its
            # duration.
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, check_wave, sura, aya, candidate
            )

            heard_len = len(result["heard_phonemes"])
            expected_len = len(result["expected_phonemes"])
            if duration_triggered:
                # No pause happened - cutting here is a guess, not a
                # response to the reciter actually stopping. Require the
                # full expected length, not just "mostly there" (that
                # threshold is fine once someone's gone quiet, but cutting
                # a still-in-progress ayah at ~85% and scoring it against
                # the full text is a guaranteed false fail on content that
                # just hadn't finished yet) - unless we've waited so long
                # that this can't be "still in progress" anymore; a real
                # gap in the recitation can keep heard_len short forever,
                # and waiting past that just risks eating the next ayah's
                # audio to make up the shortfall instead.
                buf_dur = len(candidate) / segmenter.sr
                overdue = buf_dur >= PROBE_MAX_FRACTION * expected_duration
                if heard_len < expected_len and not overdue:
                    continue
            else:
                complete_enough = heard_len >= COMPLETENESS_RATIO * expected_len
                if not complete_enough:
                    if not segmenter.is_long_silence():
                        # Looks like a breath, not the end of the ayah:
                        # don't report anything, keep listening.
                        segmenter.resume()
                        continue
                    # Else: a VAD pause long enough that it's clearly not
                    # a breath - fall through and finalize anyway.

            # The ayah before this one failed, so this segment is
            # ambiguous: a retry, or they moved on anyway. Check both and
            # take whichever one actually matches.
            if fallback_sura is not None:
                fallback_result = await loop.run_in_executor(
                    None, check_wave, fallback_sura, fallback_aya, candidate
                )
                if len(fallback_result["mismatches"]) < len(result["mismatches"]):
                    log_result(result, skipped=True)
                    result = fallback_result
                    sura, aya = fallback_sura, fallback_aya

            segmenter.finalize()
            last_probe_at = time.monotonic()
            log_result(result)

            await ws.send_json(
                {
                    "sura": result["sura"],
                    "aya": result["aya"],
                    "uthmani": result["uthmani"],
                    "passed": result["passed"],
                    "mismatches": result["mismatches"],
                }
            )

            if result["passed"]:
                fallback_sura, fallback_aya = None, None
                current = Aya(sura, aya)
                if current.is_last():
                    save_state(sura, aya)
                    await ws.send_json({"info": "last ayah of the Quran reached"})
                else:
                    nxt = current.step(1).get()
                    sura, aya = nxt.sura_idx, nxt.aya_idx
                    save_state(sura, aya)
                    expected_duration = estimate_duration_s(sura, aya)
            else:
                save_state(sura, aya)
                current = Aya(sura, aya)
                if current.is_last():
                    fallback_sura, fallback_aya = None, None
                else:
                    nxt = current.step(1).get()
                    fallback_sura, fallback_aya = nxt.sura_idx, nxt.aya_idx
                    # Probing now has to watch for either candidate
                    # finishing - use whichever is shorter so the start
                    # threshold and the overdue cap don't end up based on
                    # the wrong (possibly much longer) one.
                    expected_duration = min(
                        expected_duration,
                        estimate_duration_s(fallback_sura, fallback_aya),
                    )
    except WebSocketDisconnect:
        pass
