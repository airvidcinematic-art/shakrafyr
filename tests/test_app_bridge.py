"""App bridge: JSON detect/shift/name used by the Tauri shell."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.app_bridge import library_filename, run_detect, run_shift  # noqa: E402
from tools.detect_tuning import cents  # noqa: E402
from tools.pitch_shift import shift_file  # noqa: E402

FIX = ROOT / "fixtures"
SINE440 = FIX / "sine_A4_440.wav"


def test_library_filename_lock_pc_without_octave():
    name = library_filename("song", "root_396", "G", 396)
    assert name == "song [root_396_G396].wav"
    assert "G4396" not in name


def test_library_filename_sharp_is_ascii():
    name = library_filename("song", "heart_639", "Ds", 639)
    assert name == "song [heart_639_Ds639].wav"


def test_detect_sine_440_json():
    out = run_detect(SINE440)
    assert "a4_hz" in out
    err = cents(out["a4_hz"], 440.0)
    assert abs(err) <= 3.0, f"A4={out['a4_hz']:.2f} ({err:+.1f} ¢)"
    assert out["duration_s"] > 1.0


def test_shift_refuses_to_overwrite_original(tmp_path: Path):
    src = tmp_path / "master.wav"
    src.write_bytes(SINE440.read_bytes())
    with pytest.raises((ValueError, SystemExit, RuntimeError)):
        run_shift(src, src, 432.0 / 440.0)
    with pytest.raises((ValueError, SystemExit, RuntimeError)):
        shift_file(src, src, 432.0 / 440.0)


def test_shift_writes_sidecar_and_holds_duration(tmp_path: Path):
    dest = tmp_path / "song [concert_432_A432].wav"
    run_shift(SINE440, dest, 432.0 / 440.0)
    assert dest.exists() and dest.stat().st_size > 0
    import wave

    with wave.open(str(SINE440), "rb") as a, wave.open(str(dest), "rb") as b:
        src_s = a.getnframes() / a.getframerate()
        dst_s = b.getnframes() / b.getframerate()
    assert abs(dst_s - src_s) <= 0.05


def test_cli_detect_prints_json():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "app_bridge.py"), "detect", str(SINE440)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert abs(cents(data["a4_hz"], 440.0)) <= 3.0
