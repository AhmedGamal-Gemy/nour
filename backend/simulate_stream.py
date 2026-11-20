"""Reference client for /ws/recite: streams a wav file as if it were a live mic.

Swap `iter_frames` for real microphone capture and this is most of a real
client. Useful on its own too: feed it a full recitation session's worth
of audio concatenated with real pauses between ayahs.

Usage:
    python -m backend.simulate_stream --sura 53 --aya 1 ws://127.0.0.1:8000/ws/recite tools/smoke_test/correct.wav
"""

import argparse
import asyncio
import json

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


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("wav")
    parser.add_argument("--sura", type=int)
    parser.add_argument("--aya", type=int)
    args = parser.parse_args()

    async with connect(args.url) as ws:
        start = {}
        if args.sura and args.aya:
            start = {"sura": args.sura, "aya": args.aya}
        await ws.send(json.dumps(start))

        for frame in iter_frames(args.wav):
            await ws.send(frame)
            await asyncio.sleep(FRAME_MS / 1000)

        msg = await ws.recv()
        print(msg)


if __name__ == "__main__":
    asyncio.run(main())
