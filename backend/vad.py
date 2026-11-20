"""Energy-based pause detection: cut a continuous stream into per-ayah chunks.

Crude on purpose, and on its own not good enough: a pause this long after
speech this long also matches a mid-ayah breath, not just the end of an
ayah. push() only signals a *candidate* cut - the caller (backend/app.py)
decides whether to finalize() (real boundary - clear the buffer) or
resume() (just a breath - keep the buffer, keep listening) based on
whether what's been heard so far is actually close to the full ayah.

Still not waqf-aware - it has no idea where the Uthmani text says a pause
is expected. That's a known simplification, not the end state.
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
        max_silence_ms: int = 2500,
    ):
        self.sr = sr
        self.frame_len = int(sr * frame_ms / 1000)
        self.silence_frames_needed = max(1, silence_ms // frame_ms)
        self.min_speech_frames = max(1, min_speech_ms // frame_ms)
        self.max_silence_frames = max(1, max_silence_ms // frame_ms)
        self.thresh = silence_rms_thresh

        self.buffer = np.zeros(0, dtype=np.float32)
        self.silence_run = 0
        self.speech_frames = 0
        self.pending = False  # a candidate cut was signaled, awaiting the caller's call

    def push(self, frame: np.ndarray) -> np.ndarray | None:
        """Feed one frame of float32 samples in [-1, 1]. Returns a *candidate*
        segment (buffer not yet cleared) once enough speech is followed by
        enough silence, else None. Call finalize() or resume() in response."""
        self.buffer = np.concatenate([self.buffer, frame])

        rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))
        if rms < self.thresh:
            self.silence_run += 1
        else:
            self.silence_run = 0
            self.speech_frames += 1

        if (
            not self.pending
            and self.speech_frames >= self.min_speech_frames
            and self.silence_run >= self.silence_frames_needed
        ):
            self.pending = True
            return self.buffer.copy()
        return None

    def is_long_silence(self) -> bool:
        """True once the silence has gone on long enough that it's not a
        breath anymore, whatever the completeness check says - a safety net
        for a stalled or abandoned attempt."""
        return self.silence_run >= self.max_silence_frames

    def finalize(self) -> np.ndarray:
        """Caller confirms this candidate is a real ayah boundary."""
        segment = self.buffer.copy()
        self.buffer = np.zeros(0, dtype=np.float32)
        self.silence_run = 0
        self.speech_frames = 0
        self.pending = False
        return segment

    def resume(self) -> None:
        """Caller decided the candidate was just a breath: keep the buffer,
        keep listening, allow the next pause to signal a new candidate."""
        self.silence_run = 0
        self.pending = False
