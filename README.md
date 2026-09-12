# ShakraFyr

Winamp-style jukebox + library converter. Detects concert pitch of a file, then retunes it to **Concert A** (default 432 Hz) or a **Solfeggio note-lock** (example: heart C5 = 528 Hz → A4 ≈ 444 Hz) without changing tempo or rewriting the original.

**v0.1.0** on local `dev`. No installer yet. No GitHub remote.

## What it does (today)

- **ADD** a wav/mp3/flac → STFT residual-histogram detect (source A4).
- **Play / Apply to Play** → ffmpeg `rubberband` sidecar (`pitch=ratio`, `tempo=1`, `formant=shifted`), then HTML audio. First shift waits; repeats are cached under `%TEMP%\convert432-play\`.
- **Preview A** = retune. **Preview B** / **Bypass** = original.
- **Queue Convert** writes `ConvertedLibrary\{stem} [{preset}_{pc}{hz}].wav`. Originals are never overwritten. Duration stays put.
- Modes: Concert A (historical A4 chips + solfeggio world A≈444) · Solfeggio lock (family tabs) · Modulation (rate — Play/Convert refuse a fake A4) · Bypass. Presets are children of the active mode. Concert default stays Verdi 432.

It will **not** set A4 = 528. That would be a ~3-semitone transpose. Heart lock is C5 = 528.

## Docs

| Doc | Purpose |
|-----|---------|
| [`docs/theory/solfeggio-concert-pitch-math.md`](docs/theory/solfeggio-concert-pitch-math.md) | Math SSOT — Optimal Note Lock, why not A=528, dual-constraint (~47.4¢) |
| [`docs/adr/001-tuning-modes.md`](docs/adr/001-tuning-modes.md) | Concert-A vs Solfeggio-lock product rules |
| [`docs/adr/002-worlds-and-modulation.md`](docs/adr/002-worlds-and-modulation.md) | Worlds 444/432, palette families, sub-audio refuse, music-AM FTO gate |
| [`docs/design/theme-neon-glass-jukebox.md`](docs/design/theme-neon-glass-jukebox.md) | Neon-glass visual SSOT (Azo Sans) |
| [`docs/git-workflow.md`](docs/git-workflow.md) | Local `main` / `dev` / worktrees |
| [`.hermes/plans/2026-09-08_195950-convert432.md`](.hermes/plans/2026-09-08_195950-convert432.md) | Implementation plan (status tail is SSOT) |

## Run

Needs: Node, Rust, Python with numpy/scipy, `ffmpeg` on PATH (rubberband filter).

```bash
cd C:/Users/shaon/Projects/Convert432
python -m pytest tests/ -q          # 45 passed (2026-09-11)
npm run tauri dev                   # window + http://localhost:1432
```

Port **1432** is mandatory (`strictPort`). **1421 is GateMaster Lite** on this machine.

CLI (same DSP the window uses):

```bash
python tools/detect_tuning.py "track.mp3" --target concert_432 --out "ConvertedLibrary/track [concert_432_A432].wav"
python tools/app_bridge.py detect "track.wav"
```

## Architecture (as built)

```
index.html (neon-glass UI)
    │ invoke
    ▼
src-tauri (Tauri 2)  pick / detect / prepare_play / convert
    │ spawn
    ▼
tools/app_bridge.py → detect_tuning.py + pitch_shift.py → ffmpeg rubberband
```

Not built yet: React, SQLite library, Rust resolver, cpal live engine, stream intercept.

## Git (local only)

| Tree | Branch | Role |
|------|--------|------|
| `C:\Users\shaon\Projects\Convert432` | `dev` | Daily — edit and run here |
| `.worktrees\main` | `main` | Frozen shell snapshot |

No `origin`. Do not push unless asked.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Blank window | Vite not on 1432, or a second app stole the port. Keep `strictPort: true`. |
| “Shifting…” a long time | First Play of a retune encodes the whole file. Wait; next play is cached. |
| Play error about python | App spawns `python` / `py -3` / `python3`. Needs numpy + scipy. |
| rubberband failed | `ffmpeg` missing the rubberband filter. |
| Access denied on rebuild | Running `convert432.exe` locks the debug binary. Stop the window first. |
