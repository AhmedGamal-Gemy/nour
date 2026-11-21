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
  4. Finalizing uses the timed decode (tools/session/timed_check.py) so it
     has each phoneme's audio position, not just its text. If the heard
     content runs past this ayah's own text - a trailing block that
     doesn't match anything in it - that block almost certainly belongs to
     whatever is recited next, not to this ayah. It's split off before
     scoring (no re-running the model on cut audio: a model that uses
     surrounding context to decode each part gets *worse*, not better,
     once that context is removed) and the matching audio is kept, not
     discarded, as the start of the next segment's buffer. Position always
     advances when a split happens, whether this ayah passed or not -
     finding a trailing block is itself evidence the reciter already moved
     on, which is exactly the case a plain pass/fail check can't tell apart
     from "stay here and keep waiting."

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
from tools.session.check import MOSHAF
from tools.session.timed_check import (
    check_wave_with_timing,
    diff_phonemes,
    find_cut_sample,
    find_phoneme_split_index,
)
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

            # check_wave_with_timing is synchronous and CPU-bound (model
            # inference); run it off the event loop or every other
            # connection - including health checks and this one's own
            # pings - freezes for its duration.
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, check_wave_with_timing, sura, aya, candidate
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

            # If a trailing block of heard content doesn't match anything
            # in this ayah's own text, it almost certainly belongs to
            # whatever's recited next. Split it off (pure string work, no
            # new model call - re-decoding cut audio loses the surrounding
            # context the model used the first time) and score this ayah
            # on just its own portion.
            split_index = find_phoneme_split_index(result)
            cut_sample = None
            if split_index is not None:
                cut_sample = find_cut_sample(result, sr=segmenter.sr)
                heard_this_ayah = result["heard_phonemes"][:split_index]
                result = {
                    **result,
                    "heard_phonemes": heard_this_ayah,
                    "mismatches": diff_phonemes(
                        result["expected_phonemes"], heard_this_ayah
                    ),
                }
                result["passed"] = len(result["mismatches"]) == 0

            # Keep the matching audio tail (if any) as the start of the
            # next segment's buffer instead of discarding it - it was
            # already recorded, no need to hear it again live.
            segmenter.finalize(keep_tail_from=cut_sample)
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

            # A split means the recitation already moved past this ayah,
            # whether it passed or not - that's direct evidence, not a
            # guess, so position advances either way. Without a split,
            # the usual rule applies: pass advances, fail stays put so
            # the next segment retries it.
            if split_index is not None or result["passed"]:
                current = Aya(sura, aya)
                # is_last() means last ayah of its *surah*, not of the
                # Quran - true end-of-Quran also needs sura_idx == 114
                # (An-Nas). Without that check, position tracking would
                # stop dead at the end of every surah instead of
                # continuing into the next one.
                at_end_of_quran = current.get().sura_idx == 114 and current.is_last()
                if at_end_of_quran:
                    save_state(sura, aya)
                    if result["passed"]:
                        await ws.send_json({"info": "last ayah of the Quran reached"})
                else:
                    nxt = current.step(1).get()
                    sura, aya = nxt.sura_idx, nxt.aya_idx
                    save_state(sura, aya)
                    expected_duration = estimate_duration_s(sura, aya)
            else:
                save_state(sura, aya)
    except WebSocketDisconnect:
        pass
