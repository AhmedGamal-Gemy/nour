"""Core comparison: one ayah, one wav, exact tashkeel match against Quran Muaalem.

No fuzzy matching: the caller declares sura/aya, we hold it to that exact
Uthmani text and let the phoneme-level model catch mismatches.
"""

import difflib

import numpy as np
import torch
from librosa.core import load

from quran_transcript import Aya, MoshafAttributes, quran_phonetizer
from quran_muaalem import Muaalem

# Common Hafs defaults (murattal).
#
# madd_monfasel_len=4 (not the README example's 2): tested against 3
# independent professional reciters on the same ayah (Al-Qadr 97:1,
# "إِنَّآ" before the following word's hamza) - all 3 showed the identical
# mismatch at 2, all 3 matched exactly at 4.
#
# madd_aared_len is deliberately left at the library's default (2), not 4.
# aared only applies when the reciter actually *stops* on that word; a
# dataset clip cut from a continuous recitation where they flowed into the
# next ayah never gets aared treatment at all, it's just natural 2-count
# madd. That's a property of the specific take, not of the text - checked
# against Al-Fatiha 1:1/1:2/1:4 (clean matches at 2) and 1:6 (needs 4) from
# the same reciter in the same recording. A fixed default can't win both;
# 2 is the safer net default on current evidence, not a settled answer.
# The real fix is context-aware (apply aared only when a genuine pause was
# detected ending the segment), not a fixed config value - future work.
MOSHAF = MoshafAttributes(
    rewaya="hafs",
    madd_monfasel_len=4,
    madd_mottasel_len=4,
    madd_mottasel_waqf=4,
    madd_aared_len=2,
)

_muaalem_by_device = {}


def detect_device() -> str:
    """cuda > mps (Apple Silicon) > cpu. torch.cuda.is_available() is False
    on a Mac GPU, so checking only that silently falls back to CPU even
    when an MPS device is sitting right there - Muaalem's engine documents
    mps as a supported device, so there's no reason not to use it."""
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_muaalem(device: str | None = None) -> Muaalem:
    device = device or detect_device()
    if device not in _muaalem_by_device:
        _muaalem_by_device[device] = Muaalem(device=device)
    return _muaalem_by_device[device]


def check_wave(
    sura: int, aya: int, wave: np.ndarray, device: str | None = None
) -> dict:
    """Same comparison as check_ayah, but on an already-loaded 16kHz mono array."""
    fmt = Aya(sura, aya).get()
    ref = quran_phonetizer(fmt.uthmani, MOSHAF, remove_spaces=True)

    muaalem = get_muaalem(device)
    out = muaalem([wave], [ref], sampling_rate=16000)[0]

    mismatches = []
    sm = difflib.SequenceMatcher(a=ref.phonemes, b=out.phonemes.text)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        mismatches.append(
            {
                "type": tag,
                "expected": ref.phonemes[i1:i2],
                "heard": out.phonemes.text[j1:j2],
            }
        )

    return {
        "sura": fmt.sura_idx,
        "aya": fmt.aya_idx,
        "uthmani": fmt.uthmani,
        "expected_phonemes": ref.phonemes,
        "heard_phonemes": out.phonemes.text,
        "mismatches": mismatches,
        "passed": len(mismatches) == 0,
    }


def check_ayah(sura: int, aya: int, wav_path: str, device: str | None = None) -> dict:
    wave, _ = load(wav_path, sr=16000, mono=True)
    return check_wave(sura, aya, wave, device=device)
