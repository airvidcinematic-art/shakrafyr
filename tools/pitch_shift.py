"""Tempo-preserving pitch shift.

One primitive: multiply every frequency by ``ratio = A4_target / A4_source``.
Duration and sample rate stay put (ffmpeg rubberband, not resample/asetrate).
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from tools.detect_tuning import load_wav_mono, write_float_wav


def decode_mono(path: str | Path) -> tuple[np.ndarray, int]:
    """Decode any ffmpeg-readable file to mono float PCM (native sample rate)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    ffmpeg = find_ffmpeg()
    with tempfile.TemporaryDirectory(prefix="c432dec_") as td:
        dst = Path(td) / "dec.wav"
        cmd = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            str(dst),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg decode failed: {proc.stderr.strip()}")
        return load_wav_mono(dst)


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found on PATH (needed for rubberband pitch shift)")
    return exe


def shift_audio(y: np.ndarray, sr: int, ratio: float) -> np.ndarray:
    """Scale all frequencies by ``ratio``. Duration and sample rate unchanged."""
    y = np.asarray(y, dtype=np.float64)
    if y.ndim != 1:
        raise ValueError("shift_audio expects mono 1-D samples")
    if abs(ratio - 1.0) < 1e-12:
        return y.copy()
    if not (0.01 <= ratio <= 100.0):
        raise ValueError(f"ratio {ratio} outside rubberband range")

    with tempfile.TemporaryDirectory(prefix="c432_") as td:
        td_path = Path(td)
        src = td_path / "in.wav"
        dst = td_path / "out.wav"
        write_float_wav(src, y, sr)
        shift_file(src, dst, ratio)
        out, out_sr = load_wav_mono(dst)
    if out_sr != sr:
        raise RuntimeError(f"sample rate changed {sr} → {out_sr}")
    return out


def shift_file(src: str | Path, dst: str | Path, ratio: float) -> None:
    """Decode ``src`` with ffmpeg, pitch-shift by ``ratio``, write ``dst``.

    Original file is never overwritten. ``ratio`` is a frequency multiplier
    (432/440), not cents and not a tempo change.
    """
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = find_ffmpeg()
    if abs(ratio - 1.0) < 1e-12:
        af = "anull"
    else:
        af = f"rubberband=pitch={ratio:.12f}:tempo=1:formant=shifted"
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-af",
        af,
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg rubberband failed ({proc.returncode}): {proc.stderr.strip()}")
    if not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError(f"ffmpeg produced no output at {dst}")
