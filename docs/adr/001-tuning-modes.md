# ADR 001 — Tuning modes: Concert-A vs Solfeggio lock

## Status

Accepted (v1 design)

## Context

Users want (a) A=432 retunes and (b) chakra/Solfeggio versions (e.g. 528 Hz “heart”).  
Setting A4 equal to a Solfeggio frequency often shifts music by multiple semitones.  
A=432 and C=528 cannot both be exact under 12-tone equal temperament.

## Decision

1. **Single DSP primitive:** global pitch ratio `A4_target / A4_source` (tempo preserved).  
2. **Mode Concert-A:** `A4_target` is a chosen concert pitch (default **432**; also 440, 432, 444, custom).  
3. **Mode Solfeggio-Lock:** `A4_target` is computed so a chosen (or auto) MIDI degree lands exactly on frequency `F` (Optimal Note Lock — see `docs/theory/solfeggio-concert-pitch-math.md`).  
4. **Never advertise dual exact locks** in one render. Dual goals → **two library files** or two playlist entries.  
5. **Safety rail:** default reject/warn when `|shift_cents| > 80`; hard confirm above 100.  
6. **Heart default:** 528 Hz locks to **C5** → A4 ≈ 443.99 Hz (+15.6 ¢ from A440).

## Consequences

- UI must show lock note, A4, and cents — not a lone “528 Hz” label.  
- Jukebox non-destructive path and convert path share `resolve_target()`.  
- Key-aware tonic lock deferred to v1.1.  
- Stream intercept still just applies the same ratio.
