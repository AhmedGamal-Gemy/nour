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

        enough_speech = self.speech_frames >= self.min_speech_frames
        long_silence = self.silence_run >= self.max_silence_frames
        if (
            not self.pending
            and self.silence_run >= self.silence_frames_needed
            and (enough_speech or long_silence)
        ):
            self.pending = True
            return self.buffer.copy()
        return None

    def is_long_silence(self) -> bool:
        """True once the silence has gone on long enough that it's not a
        breath anymore, whatever the completeness check says - a safety net
        for a stalled or abandoned attempt."""
        return self.silence_run >= self.max_silence_frames

    def finalize(self, keep_tail_from: int | None = None) -> np.ndarray:
        """Caller confirms this candidate is a real ayah boundary. Returns
        the full segment that was checked. If keep_tail_from is given (a
        sample index into that segment), the buffer isn't cleared to empty -
        it's reset to segment[keep_tail_from:], the part of this audio that
        actually belongs to whatever comes next. That audio was already
        recorded; reusing it as the start of the next segment means it
        doesn't need to be heard again live, and no real content is lost
        between one ayah and the next."""
        segment = self.buffer.copy()
        if keep_tail_from is None:
            self.buffer = np.zeros(0, dtype=np.float32)
        else:
            self.buffer = segment[keep_tail_from:].copy()
        self.silence_run = 0
        self.speech_frames = 0
        self.pending = False
        return segment

    def resume(self) -> None:
        """Caller decided the candidate was just a breath: keep the buffer,
        keep listening. Also resets speech_frames, not just silence_run - a
        candidate shouldn't fire again every silence_ms for as long as the
        breath continues, only once real speech resumes (or is_long_silence
        trips as a safety net for a stalled attempt)."""
        self.silence_run = 0
        self.speech_frames = 0
        self.pending = False
