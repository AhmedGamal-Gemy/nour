"""Energy-based pause detection: cut a continuous stream into per-ayah chunks.

Crude on purpose for a first pass. It does not know what a waqf mark is -
it just waits for enough quiet after enough speech. Good enough to prove
the streaming pipeline; the real "segment at waqf marks" rule (PLAN-level
design constraint, not negotiable later) needs a proper VAD or the
model's own timing output, not this.
"""

import numpy as np


class SilenceSegmenter:
    def __init__(
        self,
        sr: int = 16000,
        frame_ms: int = 20,
        silence_ms: int = 600,
        min_speech_ms: int = 500,
        silence_rms_thresh: float = 0.01,
    ):
        self.sr = sr
        self.frame_len = int(sr * frame_ms / 1000)
        self.silence_frames_needed = max(1, silence_ms // frame_ms)
        self.min_speech_frames = max(1, min_speech_ms // frame_ms)
        self.thresh = silence_rms_thresh

        self.buffer = np.zeros(0, dtype=np.float32)
        self.silence_run = 0
        self.speech_frames = 0

    def push(self, frame: np.ndarray) -> np.ndarray | None:
        """Feed one frame of float32 samples in [-1, 1]. Returns a finished
        segment once enough speech is followed by enough silence, else None."""
        self.buffer = np.concatenate([self.buffer, frame])

        rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))
        if rms < self.thresh:
            self.silence_run += 1
        else:
            self.silence_run = 0
            self.speech_frames += 1

        if (
            self.speech_frames >= self.min_speech_frames
            and self.silence_run >= self.silence_frames_needed
        ):
            segment = self.buffer.copy()
            self.buffer = np.zeros(0, dtype=np.float32)
            self.silence_run = 0
            self.speech_frames = 0
            return segment
        return None
