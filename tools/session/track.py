"""Position tracking: declare a starting ayah once, then run one clip per call.

Usage:
    python -m tools.session.track --sura 53 --aya 1 --wav clip1.wav   # starts position
    python -m tools.session.track --wav clip2.wav                     # resumes saved position

On a pass, advances to the next ayah and saves it. On a fail, stays put so
you can retry the same ayah. Every attempt is appended to data/results.jsonl.
"""

import argparse
import datetime
import json
import pathlib

from quran_transcript import Aya

from .check import check_ayah

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
STATE_PATH = ROOT / "data" / "session_state.json"
LOG_PATH = ROOT / "data" / "results.jsonl"


def load_state() -> dict | None:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return None


def save_state(sura: int, aya: int) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"sura": sura, "aya": aya}))


def log_result(result: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "date": datetime.date.today().isoformat(),
        "sura": result["sura"],
        "aya": result["aya"],
        "passed": result["passed"],
        "mismatches": result["mismatches"],
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sura", type=int)
    parser.add_argument("--aya", type=int)
    parser.add_argument("--wav", required=True, help="Clip for the current ayah")
    parser.add_argument("--device")
    args = parser.parse_args()

    if args.sura and args.aya:
        sura, aya = args.sura, args.aya
    else:
        state = load_state()
        if state is None:
            parser.error("No saved position yet - pass --sura and --aya to start.")
        sura, aya = state["sura"], state["aya"]

    result = check_ayah(sura, aya, args.wav, device=args.device)
    log_result(result)

    print(f"{result['sura']}:{result['aya']}  {result['uthmani']}")
    if result["passed"]:
        print("PASS")
        current = Aya(sura, aya)
        if current.is_last():
            print("That was the last ayah of the Quran.")
        else:
            nxt = current.step(1).get()
            save_state(nxt.sura_idx, nxt.aya_idx)
            print(f"Next: {nxt.sura_idx}:{nxt.aya_idx}")
    else:
        print("FAIL - staying on this ayah")
        for m in result["mismatches"]:
            print(f"  {m['type']}: expected {m['expected']!r} -> heard {m['heard']!r}")
        save_state(sura, aya)


if __name__ == "__main__":
    main()
