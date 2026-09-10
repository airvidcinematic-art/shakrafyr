# Convert432

Winamp-style jukebox + library converter for **Concert-A** (default 432 Hz) and **Solfeggio note-lock** tunings (e.g. heart: C5 = 528 Hz → A4 ≈ 444 Hz).

## Docs

| Doc | Purpose |
|-----|---------|
| [`docs/theory/solfeggio-concert-pitch-math.md`](docs/theory/solfeggio-concert-pitch-math.md) | Math SSOT — Optimal Note Lock, why not A=528, dual-constraint proof |
| [`docs/adr/001-tuning-modes.md`](docs/adr/001-tuning-modes.md) | Concert-A vs Solfeggio-lock product rules |
| [`.hermes/plans/2026-09-08_195950-convert432.md`](.hermes/plans/2026-09-08_195950-convert432.md) | Implementation plan |

## Core idea (one sentence)

Detect source A4 → choose target A4 (fixed concert pitch **or** the A4 that makes a chosen note equal a Solfeggio Hz with minimal cents shift) → pitch-shift by `target/source` without changing tempo or rewriting the original file.

## Status

Detector + tempo-preserving pitch shift are live (ffmpeg `rubberband`, not resample). Desktop window on **port 1432**.

```bash
python tools/detect_tuning.py "track.mp3" --target concert_432 --out "ConvertedLibrary/track [concert_432_A432].wav"
python -m pytest tests/ -q
npm run tauri dev   # Convert432 window; http://localhost:1432
```

In the app: **ADD** a file → detect A4 → **Play** / **Apply to Play** (shifts to a temp sidecar, original untouched) → **Queue Convert** writes `ConvertedLibrary/`. Preview A = retune, Preview B = original. Git: `main` stable, `dev` daily (this tree). No remote until you ask.
