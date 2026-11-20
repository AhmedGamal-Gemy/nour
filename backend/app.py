"""Realtime recitation check over a WebSocket.

Protocol on /ws/recite:
  1. Client sends one JSON text message to start or resume:
       {"sura": 53, "aya": 1}
     or {} to resume the last saved position (data/session_state.json).
  2. Client then streams binary frames: raw PCM16LE, mono, 16kHz. Frame
     size isn't fixed, but small (~20ms, 640 bytes) is what the pause
     detector in vad.py is tuned around.
  3. Whenever the segmenter signals a candidate pause, the server checks
     the buffered audio so far against the reference. If what's been heard
     is clearly shorter than the expected ayah, it's treated as a breath:
     nothing is sent, the buffer is kept, and listening continues. Only
     once the heard content is close to the full expected length (or the
     silence has gone on long enough that it's clearly not a breath
     anymore) does it finalize and send one JSON message:
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

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from quran_transcript import Aya

from backend.vad import SilenceSegmenter
from tools.session.check import check_wave
from tools.session.track import load_state, log_result, save_state

# How close the heard phoneme count must be to the expected count before a
# pause is treated as the end of the ayah rather than a breath. Length, not
# content, on purpose - a tashkeel mistake doesn't change how many phonemes
# were said, only which ones, so this doesn't mask the thing we're checking for.
COMPLETENESS_RATIO = 0.85

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

    try:
        while True:
            chunk = await ws.receive_bytes()
            frame = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            candidate = segmenter.push(frame)
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
            if not complete_enough and not segmenter.is_long_silence():
                # Looks like a breath, not the end of the ayah: don't report
                # anything, keep the buffer, keep listening.
                segmenter.resume()
                continue

            segmenter.finalize()
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
            else:
                save_state(sura, aya)
    except WebSocketDisconnect:
        pass
