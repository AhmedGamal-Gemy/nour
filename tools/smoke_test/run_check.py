"""Smoke test: compare a recitation clip against the exact Uthmani text.

Usage:
    python run_check.py --sura 1 --aya 1 --wav correct.wav

No fuzzy matching: the user declares which ayah they recited, and we hold
it to that exact text with tashkeel, letting Quran Muaalem catch mismatches
at the phoneme/tashkeel level.
"""

import argparse

import torch
from librosa.core import load

from quran_transcript import Aya, MoshafAttributes, quran_phonetizer
from quran_muaalem import Muaalem, explain_for_terminal

# Common Hafs defaults (murattal). Revisit once we care about a specific
# reciter style; these do not change the hard "exact tashkeel" comparison.
MOSHAF = MoshafAttributes(
    rewaya="hafs",
    madd_monfasel_len=2,
    madd_mottasel_len=4,
    madd_mottasel_waqf=4,
    madd_aared_len=2,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sura", type=int, required=True)
    parser.add_argument("--aya", type=int, required=True)
    parser.add_argument("--wav", required=True)
    parser.add_argument(
        "--device", default="cuda" if torch.cuda.is_available() else "cpu"
    )
    args = parser.parse_args()

    uthmani = Aya(args.sura, args.aya).get().uthmani
    print(f"Reference ({args.sura}:{args.aya}): {uthmani}\n")

    ref = quran_phonetizer(uthmani, MOSHAF, remove_spaces=True)

    muaalem = Muaalem(device=args.device)
    wave, _ = load(args.wav, sr=16000, mono=True)
    out = muaalem([wave], [ref], sampling_rate=16000)[0]

    explain_for_terminal(
        phonemes=out.phonemes.text,
        exp_phonemes=ref.phonemes,
        sifat=out.sifat,
        exp_sifat=ref.sifat,
    )


if __name__ == "__main__":
    main()
