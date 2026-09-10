"""Detector contract: residual-histogram concert A4.

Golden fixtures (sines / ET chords) stay inside the theory tolerances.
The clutter case is the regression lock from docs/audit/tuning-detection-audit.md:
a loud detuned voice must not outvote the rest of an A432 chord.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.detect_tuning import cents, estimate_tuning, load_wav_mono  # noqa: E402

FIX = ROOT / "fixtures"
HEART_A4 = 528.0 / (2 ** (3 / 12.0))  # C5=528 ⇒ A4 ≈ 443.993


def _a4(path: Path) -> float:
    y, sr = load_wav_mono(path)
    return estimate_tuning(y, sr)["a4_hz"]


def make_clutter_a432(sr: int = 44100, seconds: float = 4.0) -> tuple[np.ndarray, int]:
    """A432 C-major-ish chord + a louder B4 detuned +45¢ + noise."""
    t = np.arange(int(sr * seconds)) / sr
    y = np.zeros_like(t)
    for midi in (60, 64, 67, 69):
        y += 0.22 * np.sin(2 * np.pi * (432.0 * 2 ** ((midi - 69) / 12.0)) * t)
    detuned_b4 = 432.0 * (2 ** (2 / 12.0)) * (2 ** (45 / 1200.0))
    y += 0.55 * np.sin(2 * np.pi * detuned_b4 * t)
    y += 0.03 * np.random.default_rng(1).standard_normal(t.size)
    return y, sr


def test_loud_detuned_intruder_does_not_outvote_A432_chord():
    y, sr = make_clutter_a432()
    a4 = estimate_tuning(y, sr)["a4_hz"]
    err = cents(a4, 432.0)
    assert abs(err) <= 5.0, (
        f"loud +45¢ intruder captured the vote: A4={a4:.2f} Hz ({err:+.1f} ¢ vs 432). "
        "Concert pitch is an ensemble property — do not magnitude-weight the residual histogram."
    )


@pytest.mark.parametrize(
    "name,truth,tol",
    [
        ("sine_A4_440.wav", 440.0, 3.0),
        ("sine_A4_432.wav", 432.0, 3.0),
        ("sine_A4_443.wav", 443.0, 3.0),
        ("sine_A4_444.wav", 444.0, 3.0),
        ("chord_Cmaj_A440.wav", 440.0, 5.0),
        ("chord_Cmaj_A432.wav", 432.0, 5.0),
        ("chord_Cmaj_A444.wav", 444.0, 5.0),
        ("chord_heart_C528.wav", HEART_A4, 5.0),
        ("stress_clutter_A432.wav", 432.0, 5.0),
        ("stress_bright_A443_hat.wav", 443.0, 5.0),
        ("stress_vibrato_A440.wav", 440.0, 8.0),
        ("stress_stretch_A440.wav", 440.0, 8.0),
    ],
)
def test_fixture_within_tolerance(name: str, truth: float, tol: float):
    path = FIX / name
    assert path.exists(), f"missing fixture {path} — run: python tools/detect_tuning.py --gen-fixtures"
    a4 = _a4(path)
    err = cents(a4, truth)
    assert abs(err) <= tol, f"{name}: A4={a4:.2f} Hz ({err:+.1f} ¢ vs {truth:.2f}, tol ±{tol})"
