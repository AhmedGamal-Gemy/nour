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

# Common Hafs defaults (murattal). Revisit once we care about a specific
# reciter style; these do not change the hard "exact tashkeel" comparison.
MOSHAF = MoshafAttributes(
    rewaya="hafs",
    madd_monfasel_len=2,
    madd_mottasel_len=4,
    madd_mottasel_waqf=4,
    madd_aared_len=2,
)

_muaalem_by_device = {}


def get_muaalem(device: str | None = None) -> Muaalem:
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
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
