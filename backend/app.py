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
     On a fail it stays on the same ayah so the next segment retries it.

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
            complete_enough = heard_len >= COMPLETENESS_RATIO * expected_len
            if not complete_enough:
                if duration_triggered:
                    # Not done yet - this was a peek, not a VAD candidate,
                    # so there's no VAD state to undo. Keep listening.
                    continue
                if not segmenter.is_long_silence():
                    # Looks like a breath, not the end of the ayah: don't
                    # report anything, keep the buffer, keep listening.
                    segmenter.resume()
                    continue
                # Else: a VAD pause that's gone on long enough that it's
                # clearly not a breath - fall through and finalize anyway.

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
    except WebSocketDisconnect:
        pass
