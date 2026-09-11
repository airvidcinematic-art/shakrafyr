#!/usr/bin/env python3
"""Convert432 tuning detection — pure numpy/scipy (no librosa).

Pipeline
--------
1. Load mono PCM (WAV via wave stdlib, or raw path decode later).
2. STFT magnitude → peak pick per frame (strong local maxima).
3. Map each peak Hz → continuous MIDI relative to A440 reference:
       midi = 69 + 12 * log2(f / 440)
4. Fractional bin residual r = midi - round(midi)  ∈ [-0.5, 0.5)
   This is the per-peak tuning offset in *semitone fractions*.
5. Histogram residuals as an **unweighted count** (resolution ~0.01 bin ≈ 1 cent).
   Do not weight by peak magnitude — a loud detuned voice must not outvote the ensemble.
6. Peak of histogram = estimated tuning offset τ (bins).
7. Concert pitch (τ in semitone fractions / 12-TET bins):
       A4_src = 440 * 2^(τ / 12)

Also reports cents from 440 and confidence (winning-bin count / total peaks).
"""

from __future__ import annotations

import argparse
import math
import sys
import wave
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
from scipy.signal import stft

from tools.resolve_target import (  # noqa: E402
    SubAudioTargetError,
    a4_for_lock,
    cents,
    resolve_target,
)


def load_wav_mono(path: str | Path) -> tuple[np.ndarray, int]:
    path = Path(path)
    with wave.open(str(path), "rb") as w:
        nch = w.getnchannels()
        sw = w.getsampwidth()
        sr = w.getframerate()
        nframes = w.getnframes()
        raw = w.readframes(nframes)
    if sw == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    elif sw == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128) / 128.0
    else:
        raise ValueError(f"unsupported sampwidth {sw}")
    if nch > 1:
        data = data.reshape(-1, nch).mean(axis=1)
    return data, sr


def write_sine_wav(path: str | Path, freq: float, sr: int = 44100, seconds: float = 2.0, amp: float = 0.5) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(sr * seconds)
    t = np.arange(n) / sr
    y = (amp * np.sin(2 * np.pi * freq * t)).astype(np.float64)
    # light harmonic to look slightly more "musical"
    y += 0.15 * amp * np.sin(2 * np.pi * (2 * freq) * t)
    y += 0.07 * amp * np.sin(2 * np.pi * (3 * freq) * t)
    pcm = np.clip(y * 32767, -32767, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def write_chord_wav(
    path: str | Path,
    a4: float,
    midis: list[int],
    sr: int = 44100,
    seconds: float = 3.0,
) -> None:
    """Equal-tempered chord at given concert A4."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(sr * seconds)
    t = np.arange(n) / sr
    y = np.zeros(n, dtype=np.float64)
    for m in midis:
        f = a4 * (2 ** ((m - 69) / 12.0))
        y += 0.25 * np.sin(2 * np.pi * f * t)
        y += 0.08 * np.sin(2 * np.pi * (2 * f) * t)
    y /= max(1e-9, np.max(np.abs(y)))
    pcm = np.clip(y * 0.7 * 32767, -32767, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def write_float_wav(path: str | Path, y: np.ndarray, sr: int = 44100) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = float(np.max(np.abs(y))) if y.size else 1.0
    pcm = np.clip(y / max(1e-9, peak) * 0.8 * 32767, -32767, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def write_stress_fixtures(fix: str | Path, sr: int = 44100) -> None:
    """Adversarial set: vibrato, loud detuned clutter, noise bursts, stretched partials."""
    fix = Path(fix)
    t = np.arange(int(sr * 4.0)) / sr

    phase = 2 * np.pi * 440.0 * np.cumsum(2.0 ** (0.08 * np.sin(2 * np.pi * 5.5 * t) / 12.0)) / sr
    write_float_wav(fix / "stress_vibrato_A440.wav", 0.5 * np.sin(phase), sr)

    y = np.zeros_like(t)
    for m in (60, 64, 67, 69):
        y += 0.22 * np.sin(2 * np.pi * (432.0 * 2 ** ((m - 69) / 12.0)) * t)
    det = 432.0 * (2 ** (2 / 12.0)) * (2 ** (45 / 1200.0))
    y += 0.55 * np.sin(2 * np.pi * det * t)
    y += 0.03 * np.random.default_rng(1).standard_normal(t.size)
    write_float_wav(fix / "stress_clutter_A432.wav", y, sr)

    y = np.zeros_like(t)
    for m in (60, 64, 67, 69, 72):
        y += 0.20 * np.sin(2 * np.pi * (443.0 * 2 ** ((m - 69) / 12.0)) * t)
    rng = np.random.default_rng(2)
    for _ in range(8):
        s = int(rng.uniform(0, len(t) - sr // 5))
        n = sr // 20
        y[s : s + n] += 0.5 * rng.standard_normal(n) * np.exp(-np.linspace(0, 8, n))
    write_float_wav(fix / "stress_bright_A443_hat.wav", y, sr)

    y = np.zeros_like(t)
    for k in range(1, 14):
        y += (1.0 / k) * np.sin(2 * np.pi * (440.0 * k * (1 + 0.00025 * k * k)) * t)
    write_float_wav(fix / "stress_stretch_A440.wav", y, sr)


def hz_to_midi(f: np.ndarray, a4_ref: float = 440.0) -> np.ndarray:
    f = np.asarray(f, dtype=np.float64)
    out = np.full_like(f, np.nan)
    mask = f > 0
    out[mask] = 69.0 + 12.0 * np.log2(f[mask] / a4_ref)
    return out


def _empty_detection() -> dict:
    return {
        "a4_hz": 440.0,
        "offset_bins": 0.0,
        "cents_from_440": 0.0,
        "confidence": 0.0,
        "n_peaks": 0,
        "method": "fallback_empty",
    }


def estimate_tuning(
    y: np.ndarray,
    sr: int,
    *,
    n_fft: int = 8192,
    hop: int = 1024,
    fmin: float = 60.0,
    fmax: float = 5000.0,
    resolution: float = 0.01,
    frame_peak_frac: float = 0.1,
    median_gate: bool = True,
) -> dict:
    """Estimate concert A4 via residual pitch-class histogram (librosa-like).

    Per-frame peaks above ``frame_peak_frac * frame max``, optional median
    magnitude cut, then an **unweighted count** histogram over residual τ.
    """
    if y.size < n_fft:
        y = np.pad(y, (0, n_fft - y.size))

    f, _t, Z = stft(y, fs=sr, nperseg=n_fft, noverlap=n_fft - hop, boundary=None)
    mag = np.abs(Z)
    residuals: list[float] = []
    peak_mags: list[float] = []
    bin_hz = float(f[1] - f[0]) if len(f) > 1 else 0.0

    for frame in range(mag.shape[1]):
        col = mag[:, frame]
        floor = frame_peak_frac * (float(col.max()) if col.size else 0.0)
        if floor <= 0.0:
            continue
        for i in range(2, len(col) - 2):
            v = col[i]
            if v < floor:
                continue
            if not (v > col[i - 1] and v > col[i + 1] and v >= col[i - 2] and v >= col[i + 2]):
                continue
            freq = f[i]
            if freq < fmin or freq > fmax:
                continue
            a, b, c = col[i - 1], col[i], col[i + 1]
            denom = (a - 2 * b + c)
            delta = 0.0 if abs(denom) < 1e-12 else 0.5 * (a - c) / denom
            freq_ref = freq + delta * bin_hz
            if freq_ref <= 0:
                continue
            midi = 69.0 + 12.0 * math.log2(freq_ref / 440.0)
            r = midi - round(midi)
            if r >= 0.5:
                r -= 1.0
            if r < -0.5:
                r += 1.0
            residuals.append(r)
            peak_mags.append(float(v))

    if not residuals:
        return _empty_detection()

    res = np.asarray(residuals, dtype=np.float64)
    mags = np.asarray(peak_mags, dtype=np.float64)
    if median_gate:
        keep = mags >= np.median(mags)
        res = res[keep]
        if res.size == 0:
            return _empty_detection()

    bins = np.arange(-0.5, 0.5 + resolution * 0.5, resolution)
    hist, edges = np.histogram(res, bins=bins)
    k = int(np.argmax(hist))
    if 0 < k < len(hist) - 1:
        a, b, c = hist[k - 1], hist[k], hist[k + 1]
        denom = (a - 2 * b + c)
        d = 0.0 if abs(denom) < 1e-12 else 0.5 * (a - c) / denom
    else:
        d = 0.0
    center = 0.5 * (edges[k] + edges[k + 1])
    tau = float(center + d * resolution)

    a4 = 440.0 * (2.0 ** (tau / 12.0))
    cents_from_440 = 1200.0 * math.log2(a4 / 440.0)
    conf = float(hist[k] / max(hist.sum(), 1e-12))

    return {
        "a4_hz": a4,
        "offset_bins": tau,
        "cents_from_440": cents_from_440,
        "confidence": conf,
        "n_peaks": int(res.size),
        "method": "stft_residual_histogram",
        "hist_peak_mass": float(hist[k]),
    }


def ratio_to_target(a4_src: float, a4_tgt: float) -> float:
    return a4_tgt / a4_src


def resolve_concert(a4_src: float, a4_tgt: float) -> dict:
    return resolve_target(a4_src=a4_src, mode="concert_a", a4_tgt=a4_tgt)


def resolve_heart_c528(a4_src: float) -> dict:
    return resolve_target(a4_src=a4_src, mode="solfeggio_lock", preset_id="heart_528")


def run_pipeline(path: str | Path, target: str = "concert_432") -> dict:
    path = Path(path)
    if path.suffix.lower() == ".wav":
        y, sr = load_wav_mono(path)
    else:
        from tools.pitch_shift import decode_mono

        y, sr = decode_mono(path)
    det = estimate_tuning(y, sr)
    a4_src = det["a4_hz"]
    res = resolve_target(a4_src=a4_src, preset_id=target)
    return {
        "path": str(path),
        "sr": sr,
        "duration_s": len(y) / sr,
        "detection": det,
        "resolve": res,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Convert432 tuning detector")
    p.add_argument("input", nargs="?", help="audio file (wav, mp3, …)")
    p.add_argument("--gen-fixtures", action="store_true", help="write test fixtures then exit")
    p.add_argument(
        "--target",
        default="concert_432",
        help="palette id (concert_432, heart_528, world_444, bypass, …). Sub-audio ids raise.",
    )
    p.add_argument("--json", action="store_true")
    p.add_argument("--out", help="write pitch-shifted copy (never overwrites the original)")
    args = p.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    fix = root / "fixtures"

    if args.gen_fixtures:
        # Pure A4 sines at known concert pitches
        for a4 in (440.0, 432.0, 443.0, 444.0):
            write_sine_wav(fix / f"sine_A4_{int(a4)}.wav", freq=a4)
        # C major triad at A440 and A432 (more realistic residual hist)
        # C4=60 E4=64 G4=67 A4=69
        write_chord_wav(fix / "chord_Cmaj_A440.wav", a4=440.0, midis=[60, 64, 67, 69])
        write_chord_wav(fix / "chord_Cmaj_A432.wav", a4=432.0, midis=[60, 64, 67, 69])
        write_chord_wav(fix / "chord_Cmaj_A444.wav", a4=444.0, midis=[60, 64, 67, 69])
        # Heart world: C5=528 implies A4≈443.993 — chord including C5
        a4_heart = 528.0 / (2 ** (3 / 12.0))
        write_chord_wav(fix / "chord_heart_C528.wav", a4=a4_heart, midis=[60, 64, 67, 69, 72])
        write_stress_fixtures(fix)
        print(f"fixtures written under {fix}")
        return 0

    if not args.input:
        p.error("input path required (or --gen-fixtures)")

    try:
        out = run_pipeline(args.input, target=args.target)
    except SubAudioTargetError as exc:
        raise SystemExit(str(exc)) from exc
    if args.json:
        import json
        print(json.dumps(out, indent=2))
    else:
        d = out["detection"]
        r = out["resolve"]
        print("=== Convert432 tuning detection ===")
        print(f"file:       {out['path']}")
        print(f"sr:         {out['sr']} Hz  duration: {out['duration_s']:.2f}s")
        print(f"method:     {d['method']}")
        print(f"peaks used: {d['n_peaks']}")
        print(f"confidence: {d['confidence']:.3f}")
        print(f"offset:     {d['offset_bins']:+.4f} bins")
        print(f"A4_src:     {d['a4_hz']:.3f} Hz  ({d['cents_from_440']:+.2f} ¢ vs A440)")
        print("--- resolve ---")
        print(f"mode:       {r['mode']}")
        print(f"lock:       {r['lock']}")
        print(f"A4_tgt:     {r['a4_target']:.3f} Hz")
        print(f"shift:      {r['shift_cents']:+.2f} ¢")
        print(f"ratio:      {r['ratio']:.8f}")
        print("(playback multiplies all frequencies by ratio; tempo unchanged)")

    if args.out:
        from tools.pitch_shift import shift_file

        dest = Path(args.out)
        src = Path(args.input)
        if dest.resolve() == src.resolve():
            raise SystemExit("refusing to overwrite the original — pick a different --out path")
        shift_file(src, dest, out["resolve"]["ratio"])
        print(f"wrote:      {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
