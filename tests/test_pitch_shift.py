"""Tempo-preserving pitch shift: ratio scales frequency, duration stays put."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.detect_tuning import cents, estimate_tuning  # noqa: E402
from tools.pitch_shift import shift_audio  # noqa: E402

SR = 44100
RATIO_440_TO_432 = 432.0 / 440.0


def _sine(freq: float, seconds: float = 2.0) -> np.ndarray:
    t = np.arange(int(SR * seconds)) / SR
    y = 0.5 * np.sin(2 * np.pi * freq * t)
    y += 0.15 * np.sin(2 * np.pi * (2 * freq) * t)
    return y.astype(np.float64)


def test_shift_preserves_duration():
    y = _sine(440.0, seconds=2.0)
    out = shift_audio(y, SR, RATIO_440_TO_432)
    # Resample-only (slow down) would stretch ~1.85% (~37 ms). We allow 50 ms padding.
    assert abs(len(out) - len(y)) / SR <= 0.05, (
        f"duration changed {len(y)/SR:.3f}s → {len(out)/SR:.3f}s — that is slowing, not retuning"
    )


def test_sine_440_shifted_to_432_detects_near_432():
    y = _sine(440.0, seconds=2.5)
    out = shift_audio(y, SR, RATIO_440_TO_432)
    a4 = estimate_tuning(out, SR)["a4_hz"]
    err = cents(a4, 432.0)
    assert abs(err) <= 5.0, f"after 440→432 shift, detector saw A4={a4:.2f} Hz ({err:+.1f} ¢ vs 432)"


def test_ratio_one_does_not_move_pitch():
    y = _sine(440.0, seconds=2.0)
    out = shift_audio(y, SR, 1.0)
    a4 = estimate_tuning(out, SR)["a4_hz"]
    err = cents(a4, 440.0)
    assert abs(err) <= 3.0, f"ratio=1 moved pitch: A4={a4:.2f} Hz ({err:+.1f} ¢)"
