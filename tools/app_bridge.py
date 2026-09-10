"""JSON IPC for the Convert432 desktop shell.

Tauri spawns this; stdout is one JSON object. Originals are never overwritten.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.detect_tuning import estimate_tuning, load_wav_mono  # noqa: E402
from tools.pitch_shift import decode_mono, shift_file  # noqa: E402


def library_filename(stem: str, preset_id: str, lock_pc: str, hz: int | float) -> str:
    """``song [root_396_G396].wav`` — pitch class without MIDI octave."""
    hz_i = int(round(float(hz)))
    return f"{stem} [{preset_id}_{lock_pc}{hz_i}].wav"


def run_detect(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".wav":
        y, sr = load_wav_mono(path)
    else:
        y, sr = decode_mono(path)
    det = estimate_tuning(y, sr)
    return {
        "path": str(path.resolve()),
        "name": path.name,
        "stem": path.stem,
        "sr": sr,
        "duration_s": len(y) / sr if sr else 0.0,
        "a4_hz": det["a4_hz"],
        "cents_from_440": det["cents_from_440"],
        "offset_bins": det["offset_bins"],
        "confidence": det["confidence"],
        "n_peaks": det["n_peaks"],
        "method": det["method"],
    }


def run_shift(src: str | Path, dest: str | Path, ratio: float) -> dict:
    src = Path(src)
    dest = Path(dest)
    if dest.resolve() == src.resolve():
        raise ValueError("refusing to overwrite the original")
    shift_file(src, dest, ratio)
    return {"src": str(src), "dest": str(dest.resolve()), "ratio": ratio}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Convert432 app bridge")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect")
    d.add_argument("path")

    s = sub.add_parser("shift")
    s.add_argument("path")
    s.add_argument("--ratio", type=float, required=True)
    s.add_argument("--out", required=True)

    n = sub.add_parser("name")
    n.add_argument("stem")
    n.add_argument("--preset-id", required=True)
    n.add_argument("--pc", required=True)
    n.add_argument("--hz", type=float, required=True)

    args = p.parse_args(argv)
    if args.cmd == "detect":
        print(json.dumps(run_detect(args.path)))
    elif args.cmd == "shift":
        print(json.dumps(run_shift(args.path, args.out, args.ratio)))
    elif args.cmd == "name":
        print(json.dumps({"filename": library_filename(args.stem, args.preset_id, args.pc, args.hz)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        raise SystemExit(1)
