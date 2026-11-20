"""Realtime recitation check over a WebSocket.

Protocol on /ws/recite:
  1. Client sends one JSON text message to start or resume:
       {"sura": 53, "aya": 1}
     or {} to resume the last saved position (data/session_state.json).
  2. Client then streams binary frames: raw PCM16LE, mono, 16kHz. Frame
     size isn't fixed, but small (~20ms, 640 bytes) is what the pause
     detector in vad.py is tuned around.
  3. Whenever the segmenter decides enough speech was followed by enough
     silence, the server runs the same exact-tashkeel check used by the
     CLI tools and sends back one JSON message:
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
            segment = segmenter.push(frame)
            if segment is None:
                continue

            # check_wave is synchronous and CPU-bound (model inference); run
            # it off the event loop or every other connection - including
            # health checks and this one's own pings - freezes for its
            # duration.
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, check_wave, sura, aya, segment
            )
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
