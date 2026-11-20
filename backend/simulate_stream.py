"""Reference client for /ws/recite: streams wav files as if from a live mic,
one continuous session, one or more ayahs in sequence.

Swap `iter_frames` for real microphone capture and this is most of a real
client.

Usage:
    python -m backend.simulate_stream --sura 53 --aya 1 ws://127.0.0.1:8000/ws/recite \
        tools/smoke_test/correct.wav tools/smoke_test/wrong.wav
"""

import argparse
import asyncio
import json
import time

import numpy as np
from librosa.core import load
from websockets.asyncio.client import connect

FRAME_MS = 20
SR = 16000
FRAME_LEN = SR * FRAME_MS // 1000
TRAILING_SILENCE_S = 1.2


def iter_frames(wav_path: str):
    wave, _ = load(wav_path, sr=SR, mono=True)
    padded = np.concatenate([wave, np.zeros(int(SR * TRAILING_SILENCE_S), dtype=np.float32)])
    pcm16 = (padded * 32767).astype(np.int16)
    for i in range(0, len(pcm16), FRAME_LEN):
        yield pcm16[i : i + FRAME_LEN].tobytes()


async def receive_loop(ws, last_msg_at: list[float]):
    try:
        async for msg in ws:
            print(msg)
            last_msg_at[0] = time.monotonic()
    except Exception:
        pass


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("wavs", nargs="+", help="one or more wav files, streamed in order")
    parser.add_argument("--sura", type=int)
    parser.add_argument("--aya", type=int)
    args = parser.parse_args()

    async with connect(args.url) as ws:
        start = {}
        if args.sura and args.aya:
            start = {"sura": args.sura, "aya": args.aya}
        await ws.send(json.dumps(start))

        last_msg_at = [time.monotonic()]
        receiver = asyncio.create_task(receive_loop(ws, last_msg_at))

        for wav_path in args.wavs:
            for frame in iter_frames(wav_path):
                await ws.send(frame)
                await asyncio.sleep(FRAME_MS / 1000)

        # Inference on CPU can take real seconds per segment, and a session
        # can have several segments (several ayahs). Wait until the server
        # has gone quiet for IDLE_S seconds, not a fixed short sleep - a
        # fixed sleep is long enough for one ayah's inference and too
        # short the moment there's more than one.
        last_msg_at[0] = time.monotonic()
        IDLE_S, MAX_WAIT_S = 5.0, 120.0
        start_wait = time.monotonic()
        while (
            time.monotonic() - last_msg_at[0] < IDLE_S
            and time.monotonic() - start_wait < MAX_WAIT_S
        ):
            await asyncio.sleep(0.5)
        receiver.cancel()


if __name__ == "__main__":
    asyncio.run(main())
