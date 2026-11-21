"""Same comparison as check_wave, but keeps per-phoneme frame timing.

Muaalem's own decode collapses CTC frames into phonemes and discards which
audio frames each phoneme came from. We need that to find the exact audio
sample where one ayah's content ends and the next one's begins - cutting
the whole buffer at an audio timestamp, not just relabeling it under a
different ayah's text. Reimplements the same greedy CTC collapse (verified
to produce byte-identical text to Muaalem's own decode) but keeps the
frame span per phoneme.
"""

import difflib

import numpy as np
import torch
from quran_muaalem.modeling.vocab import PAD_TOKEN_IDX
from quran_transcript import Aya, quran_phonetizer

from .check import MOSHAF, get_muaalem

# Measured empirically (96 frames for 3.84s of 16kHz audio): the model
# downsamples audio to this many CTC frames per second, regardless of input
# length. Not documented by the library; re-measure if the model changes.
FRAME_RATE_HZ = 25.0


def _greedy_ctc_decode_with_spans(
    probs: torch.Tensor, id_to_vocab: dict, blank_id: int = PAD_TOKEN_IDX
) -> tuple[str, list[tuple[int, int]]]:
    """probs: (seq_len, num_classes) for one sequence. Returns the collapsed
    text and, for each phoneme, the (start_frame, end_frame) span of CTC
    frames that collapsed into it."""
    ids = probs.topk(1, dim=-1).indices.squeeze(-1).tolist()

    tokens: list[int] = []
    spans: list[tuple[int, int]] = []
    start = None
    for i, cur in enumerate(ids):
        if cur == blank_id:
            start = None
            continue
        if start is None:
            start = i
        nxt = ids[i + 1] if i + 1 < len(ids) else None
        if nxt != cur:
            tokens.append(cur)
            spans.append((start, i + 1))
            start = None

    text = "".join(id_to_vocab[t] for t in tokens)
    return text, spans


def check_wave_with_timing(
    sura: int, aya: int, wave: np.ndarray, device: str | None = None
) -> dict:
    fmt = Aya(sura, aya).get()
    ref = quran_phonetizer(fmt.uthmani, MOSHAF, remove_spaces=True)
    muaalem = get_muaalem(device)

    features = muaalem.processor([wave], sampling_rate=16000, return_tensors="pt")
    features = {
        k: v.to(muaalem.device, dtype=muaalem.dtype) for k, v in features.items()
    }
    with torch.no_grad():
        outs = muaalem.model(**features, return_dict=False)[0]
    probs = (
        torch.nn.functional.softmax(outs["phonemes"], dim=-1)
        .cpu()
        .to(torch.float32)[0]
    )

    heard, spans = _greedy_ctc_decode_with_spans(
        probs, muaalem.multi_level_tokenizer.id_to_vocab["phonemes"]
    )
    phoneme_times = [(s / FRAME_RATE_HZ, e / FRAME_RATE_HZ) for s, e in spans]

    mismatches = []
    sm = difflib.SequenceMatcher(a=ref.phonemes, b=heard)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        mismatches.append(
            {
                "type": tag,
                "expected": ref.phonemes[i1:i2],
                "heard": heard[j1:j2],
            }
        )

    return {
        "sura": fmt.sura_idx,
        "aya": fmt.aya_idx,
        "uthmani": fmt.uthmani,
        "expected_phonemes": ref.phonemes,
        "heard_phonemes": heard,
        "phoneme_times": phoneme_times,
        "mismatches": mismatches,
        "passed": len(mismatches) == 0,
    }


def find_cut_sample(result: dict, sr: int = 16000) -> int | None:
    """Given a check_wave_with_timing() result, find the audio sample where
    the heard content stops matching the reference and an unexplained tail
    begins - the likely start of the next ayah's audio bleeding into this
    buffer. Returns None if there's no such tail (nothing to cut)."""
    heard = result["heard_phonemes"]
    sm = difflib.SequenceMatcher(a=result["expected_phonemes"], b=heard)
    opcodes = sm.get_opcodes()

    # Last matched position in `heard` across all equal-tagged blocks.
    last_equal_end = 0
    for tag, _, _, j1, j2 in opcodes:
        if tag == "equal":
            last_equal_end = max(last_equal_end, j2)

    # Nothing after the last match, or it's the very end: no tail to cut.
    if last_equal_end == 0 or last_equal_end >= len(heard):
        return None

    phoneme_times = result["phoneme_times"]
    if last_equal_end > len(phoneme_times):
        return None

    cut_time_s = phoneme_times[last_equal_end - 1][1]
    return int(cut_time_s * sr)
