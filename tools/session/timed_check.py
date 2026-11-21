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


def find_phoneme_split_index(result: dict) -> int | None:
    """Given a check_wave_with_timing() result, find the index into
    heard_phonemes where a trailing, genuinely-extra block begins - the
    likely start of the next ayah's content bleeding into this buffer.
    Returns None if there's no such tail (nothing to split off).

    Anchored on the start of the trailing *insert*, not the last matched
    position: a dropped ending (an expected-but-missing stretch) is a
    "delete" with no audio behind it at all, so it can't anchor a cut -
    only heard content (equal or insert) has a real time position, and
    only the trailing block is safe to assume belongs to what's next
    rather than being a genuine gap inside this ayah."""
    heard = result["heard_phonemes"]
    sm = difflib.SequenceMatcher(a=result["expected_phonemes"], b=heard)
    opcodes = sm.get_opcodes()
    if not opcodes:
        return None
    last_tag, _, _, last_j1, _ = opcodes[-1]
    return last_j1 if last_tag == "insert" else None


def find_cut_sample(result: dict, sr: int = 16000) -> int | None:
    """Same split as find_phoneme_split_index, expressed as an audio sample
    index instead of a phoneme index - for resetting the live audio buffer,
    not for scoring (use split_index + diff_phonemes for that)."""
    split_index = find_phoneme_split_index(result)
    if split_index is None:
        return None

    phoneme_times = result["phoneme_times"]
    if split_index == 0:
        return 0
    if split_index > len(phoneme_times):
        return None

    cut_time_s = phoneme_times[split_index - 1][1]
    return int(cut_time_s * sr)


def diff_phonemes(expected: str, heard: str) -> list[dict]:
    """Pure string diff, no model call - for scoring a slice of an
    already-decoded heard_phonemes string against a different ayah's
    reference (e.g. the two halves either side of a phoneme split)."""
    mismatches = []
    sm = difflib.SequenceMatcher(a=expected, b=heard)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        mismatches.append(
            {"type": tag, "expected": expected[i1:i2], "heard": heard[j1:j2]}
        )
    return mismatches
