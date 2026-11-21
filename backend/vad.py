"""Energy-based pause detection: cut a continuous stream into per-ayah chunks.

Crude on purpose, and on its own not good enough: a pause this long after
speech this long also matches a mid-ayah breath, not just the end of an
ayah. push() only signals a *candidate* cut - the caller (backend/app.py)
decides whether to finalize() (real boundary - clear the buffer) or
resume() (just a breath - keep the buffer, keep listening) based on
whether what's been heard so far is actually close to the full ayah.

Still not waqf-aware - it has no idea where the Uthmani text says a pause
is expected. That's a known simplification, not the end state.

The silence threshold is adaptive, not fixed: tested against a real,
noisy, crowd-recorded clip (background ~0.03 RMS, not the near-zero floor
of studio reciter audio) and a fixed 0.01 threshold never fired once
during 8.6s of real recorded speech - only in artificial silence padded
on afterward. On real mic recordings, "quiet" only makes sense relative
to that recording's own ambient noise, not a fixed number tuned on clean
audio.
"""

from collections import deque

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
        noise_floor_window_s: float = 3.0,
        noise_floor_margin: float = 1.8,
    ):
        self.sr = sr
        self.frame_len = int(sr * frame_ms / 1000)
        self.silence_frames_needed = max(1, silence_ms // frame_ms)
        self.min_speech_frames = max(1, min_speech_ms // frame_ms)
        self.max_silence_frames = max(1, max_silence_ms // frame_ms)
        # Absolute floor, not the whole story: see _is_silence. Keeps very
        # clean audio (near-zero ambient noise) from becoming hypersensitive
        # to tiny variations that aren't really "quieter than usual".
        self.min_thresh = silence_rms_thresh
        self.noise_floor_margin = noise_floor_margin
        self._rms_history: deque[float] = deque(
            maxlen=max(1, int(noise_floor_window_s * 1000 / frame_ms))
        )

        self.buffer = np.zeros(0, dtype=np.float32)
        self.silence_run = 0
        self.speech_frames = 0
        self.pending = False  # a candidate cut was signaled, awaiting the caller's call

    def _is_silence(self, rms: float) -> bool:
        """A frame is "silence" if it's quieter than this recording's own
        recent ambient noise, not just below a fixed number. Noise floor is
        the 10th percentile of the last noise_floor_window_s of frames - low
        enough to track the ambient floor rather than average speech level,
        robust enough not to chase the single quietest outlier frame."""
        self._rms_history.append(rms)
        if len(self._rms_history) < self._rms_history.maxlen:
            # Not enough history yet to estimate a floor - fall back to the
            # fixed threshold rather than guessing from a handful of frames.
            return rms < self.min_thresh
        noise_floor = float(np.percentile(self._rms_history, 10))
        return rms < max(self.min_thresh, noise_floor * self.noise_floor_margin)

    def push(self, frame: np.ndarray) -> np.ndarray | None:
        """Feed one frame of float32 samples in [-1, 1]. Returns a *candidate*
        segment (buffer not yet cleared) once enough speech is followed by
        enough silence, else None. Call finalize() or resume() in response."""
        self.buffer = np.concatenate([self.buffer, frame])

        rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))
        if self._is_silence(rms):
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
