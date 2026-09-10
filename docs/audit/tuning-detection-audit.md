# Tuning-detector audit & open-source survey (Convert432)

Date: 2026-09-09 · Status: **fix landed** — unweighted count histogram + per-frame 0.1·colmax gate + median mag cut in `tools/detect_tuning.py`. Regression: `tests/test_detect_tuning.py` (clutter case was RED at +44.3¢, now GREEN). Stress wavs live in `fixtures/stress_*.wav` (`python tools/detect_tuning.py --gen-fixtures`).
Repro: `convert432_audit.py` (temp harness) over `fixtures/*.wav` + generated `fixtures/_audit/stress_*.wav`

## What we compared

Six aggregation strategies on the **same** STFT peak-picking core where possible, so score
differences come from the *voting statistic*, not the FFT:

| Variant | Histogram weighting | Gate |
|---|---|---|
| **current (shipped)** `tools/detect_tuning.py` | per-peak **magnitude** | global −40 dB floor, whole file |
| librosa-style 2048 / 8192 | **count (unweighted)** | per-frame 0.1·colmax + **median** magnitude cut |
| essentia-style 2-stage | per-frame weighted → frame-energy global | 0.1·colmax |
| proposed frame-normalized | per-frame normalized mass | 0.05·colmax + −60 dB floor |
| frame-median robust | per-frame vote → energy median | 0.05·colmax + −60 dB floor |

Fixtures: 8 known (sines/chords at A440/432/443/444 + heart C5=528 world) plus 4 stress files
(vibrato, loud detuned clutter, noise-burst hats, inharmonic stretch).

## Results — mean |error| vs truth (cents)

| Variant | Mean | Worst case |
|---|---|---|
| **librosa-style 8192** | **1.64** | −1.2 on clutter |
| frame-median robust | 4.49 | +44.3 on clutter |
| proposed frame-normalized | 4.71 | +44.3 on clutter |
| **current (shipped)** | **4.77** | **+44.3 on clutter** |
| essentia-style 2-stage | 4.80 | +44.3 on clutter |
| librosa-style 2048 | 7.26 | +42.8 on clutter |

`stress_clutter_A432.wav`: A432 major-ish chord + a **loud detuned B4 (+45¢) + noise**.
Every magnitude-weighted variant locks onto the loud intruder and reports ≈ A443 (+44¢ wrong).
Only the **unweighted count** histogram survives (4 chord notes outvote 1 intruder).

## Root cause (causal ablation on the clutter fixture)

| Weighting | Median gate | Result |
|---|---|---|
| magnitude | off | **+12¢ wrong** |
| magnitude | on | **+12¢ wrong** |
| **count** | off | −33¢ → A4 ≈ 431.7 ✓ |
| **count** | on | −33¢ → A4 ≈ 431.7 ✓ |

**The shipped detector's flaw is per-peak magnitude weighting.** Concert pitch is an *ensemble*
property — every note is evidence. Weighting peaks by loudness lets one loud section (solo
voice, bass drop, detuned lead) outvote the rest of the arrangement. librosa's `estimate_tuning`
never weights by magnitude; that is precisely why it is robust. (Essentia's `TuningFrequency`
weights within each frame — in our bench it fails the same way as shipped: the loudest peak
wins the frame vote.)

## The three deltas between our code and librosa

1. **Magnitude-weighted histogram** — HARMFUL (proven above). librosa counts peaks, unweighted.
2. **Global −40 dB floor over the whole file** — lets a quiet intro contribute nothing and a loud
   chorus dominate; librosa gates per frame at `0.1 × frame max`, then keeps peaks ≥ median mag.
3. **n_fft 8192 / hop 1024 vs librosa default 2048** — HELPFUL; at 44.1 kHz, 2048 gives ~21.5 Hz
   bins, wider than a semitone below ~C4. librosa-style @2048 was the worst variant (7.26¢ mean);
   @8192 was the best (1.64¢).

Our additions that are worth keeping: **parabolic refinement on the histogram peak** (librosa
returns the left bin edge, quantizing to 1¢) and 0.01-bin resolution.

## Recommendation

Keep the pure-numpy/scipy detector (no heavy deps in the Tauri app) but make it a faithful
librosa-style estimator:

- per-frame peaks above `0.1 × frame max` (parabolic-refined, fmin 60 / fmax 5000)
- drop the global −40 dB floor
- **drop magnitude weights** — plain count histogram over τ
- optional median magnitude cut over all peaks (librosa parity; helps real-music noise floors)
- keep n_fft 8192, hop 1024, 0.01 resolution, parabolic peak refine
- keep confidence = winning-bin mass / total (now interpretable: fraction of all peaks voting together)

Expected: ~1–2¢ mean error across the suite incl. the clutter stress case. Follow up TDD:
extend the fixture set with the `_audit` stress files, lock the golden vectors, then swap the
histogram step.

## Open-source engine survey ("can we steal something better?")

For the **global concert-pitch offset** problem (one A4 per track from polyphonic audio), the
field has exactly three relevant paradigms; the deep F0 models everyone names are the wrong
tool:

| Engine | License | What it actually does | Verdict for us |
|---|---|---|---|
| **librosa `estimate_tuning` / `pitch_tuning`** | ISC | STFT peak → residual histogram, **unweighted** | The reference implementation; permissive; we may copy outright (we already modeled on it). **Adopt its counting scheme.** |
| **essentia `TuningFrequency`** | AGPL-3.0 | Per-frame cents hist → frame-energy global vote | AGPL contaminates a closed/Tauri app; algorithm is magnitude-happy (fails our clutter). Study-only. |
| **aubio `pitch`** | GPL-3.0 | Per-frame F0 tracker (YIN/schmitt/spectral) | No global tuning estimator; GPL. You'd still build the histogram yourself. |
| **CREPE / SPICE / pYIN / YIN** | various (mostly open) | Monophonic **F0** of the melody | Wrong abstraction for a mix; and not a tuning-grid estimator. Overkill + heavy (TF/torch). |
| **Spotify basic-pitch** | Apache-2.0 | Polyphonic note transcription (TF) | Could infer a grid from transcribed notes, but ~100× the compute and tuned for MIDI, not cents-level A4. Wrong layer. |
| **olaf** | — | Onset detection | Irrelevant (not pitch). |

Bottom line: nothing better exists to "steal" for this specific problem — librosa (ISC) already
is the canonical answer and our code is 90% of the way there. The win is not a new engine; it is
**removing magnitude weighting** and **matching librosa's frame/median gating at n_fft 8192**.

## Repo hygiene

Stress fixtures are now first-class: `fixtures/stress_*.wav`, regenerated by `--gen-fixtures`.
The clutter case is locked in `tests/test_detect_tuning.py`.
