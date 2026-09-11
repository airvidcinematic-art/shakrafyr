# ADR 002 — Worlds, palette families, modulation rates

## Status

Accepted (2026-09-11)

## Context

Research census (handoff 2026-09-11): rendering the library at A4≈443.99 (already produced by `heart_528` / C5=528) puts 11/34 market tones on 12-TET degrees vs 2/34 at A=432. Sub-audio targets (Schumann 7.83, gamma 40, …) sent through Optimal Note Lock emit absurd concert pitches (7.83 → A4≈52.67 Hz, −3674¢). AM-on-music sits in Brain.fm’s patent family (US7674224B2 + 2025 continuations).

## Decision

1. **DSP primitive unchanged:** `ratio = A4_target / A4_src`. Worlds are framing, not a second engine.
2. **Two concert worlds, one app default:**
   - `world_444` (solfeggio world, A4≈443.993) — default *lock* world. `heart_528` keeps its id (library names) and carries `world=world_444`.
   - `world_432` (Cosmic / Verdi, A4=432) — default *Concert A* product preset (`verdi_432` / `concert_432`). Not sold as “the solfeggio tuning”.
   - `world_440` remains the modern-standard world (owns Newgrange 110 Hz).
3. **`resolve_target()` refuses F < 60 Hz.** 40 Hz and 7.83 Hz raise `SubAudioTargetError` instead of returning an A4. Role field on the palette: `degree-lock | modulation-rate | physical-vibration` (40 Hz is all three; default path is still raise).
4. **Modulation mode is a rate, not a retune.** Play/Convert do not invent a ratio. Shippable now: binaural pair + isochronic gate of a *standalone tone*, Cousto octave-lift of the rate into an audible drone tone. **Music-AM** (`music_am.ship=false`, flag `music_am_disabled`) waits on FTO — do not amplitude-modulate the mixed track.
5. **Palette families** (data in `tools/palette.py`): solfeggio, Cosmic Octave, numeric locks (Hz labels only), archaeoacoustics, instrument/standards, extended set, geophysical rates. UI uses family tabs. No Rife disease lists.
6. **Copy constraints:** no named diseases; no DNA-repair / water-cymatics claims; no “Hypogeum resonance” label (Hal Saflieni measured 70/114 Hz; 110–112 Hz is the wider Jahn 1995 survey). 194.18 Hz is the *solar* day; 194.71 Hz is sidereal. Do not cite a 432 Hz study “Verdiyev 2019” (does not exist).

## Consequences

- Tests in `tests/test_resolve_target.py` are the regression lock (111/888 exact A=444, OM 136.10, 2172 edge, 40 and 7.83 raise, music-AM disabled).
- Key-aware tonic lock remains v1.1. World is fixed-concert, not key-relative.
- Tone-gating / binaural *encode* of a generated tone is a later DSP slice; this ADR only ships the resolver, the refuse path, and honest UI.
