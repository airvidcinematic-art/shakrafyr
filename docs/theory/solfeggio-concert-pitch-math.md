# Solfeggio × Concert Pitch Math (Convert432)

## The problem in plain English

People ask for two different things and blur them together:

1. **Concert-pitch retune** — “Play this Beatles track so **A** is 432 Hz.”  
   One global stretch. Key stays the same. Every note moves by the same ratio.

2. **Solfeggio lock** — “Make the track so **528 Hz** is a real note in the tuning (heart / MI).”  
   528 is not “A.” Forcing **A4 = 528** (or 639, 741, 852, 963) yanks the whole song by several semitones. That is a **transpose**, not a gentle retune. It will sound wrong for Octopus’s Garden.

Convert432 treats these as **two modes** with one shared engine: *pick a target A4, then pitch-shift by `target_A4 / detected_A4`.* The music theory lives entirely in **how we choose target A4**.

---

## Fixed facts (12-TET)

Equal temperament, one free parameter: the frequency of A4.

```
freq(midi_n, A4) = A4 × 2^((midi_n − 69) / 12)
```

MIDI: A4 = 69, C4 = 60, C5 = 72, …

**Cents** between two concert pitches:

```
cents(a, b) = 1200 × log2(a / b)
```

| Move | Ratio | Cents |
|------|-------|-------|
| A440 → A432 | 432/440 ≈ 0.98182 | **−31.77 ¢** |
| A440 → A444 | 444/440 | **+15.67 ¢** |

A shift under ~±50 ¢ is a “retune.” A shift of ±100 ¢ is a full semitone (key change feel). We design Solfeggio modes to stay in the retune band whenever possible.

---

## Why “A = 936” is the wrong question

Solfeggio set (common modern list):

| Name | Hz | Naïve “put it on A4” | Result |
|------|-----|----------------------|--------|
| UT | 174 | A4=174 | ~−16 semitones — unusable |
| RE | 417 | A4=417 | ~−1 semitone |
| MI / heart | 528 | A4=528 | ~+3.2 semitones |
| FA | 639 | A4=639 | ~+6.5 semitones |
| SOL | 741 | A4=741 | ~+9 semitones |
| LA | 852 | A4=852 | ~+11.4 → almost an octave |
| SI | 963 | A4=963 | ~+13.5 semitones |

**Rule:** a Solfeggio number is a **target absolute frequency for some scale degree**, not a new A4 by default.

---

## Core algorithm: Optimal Note Lock

Given:

- `F` — Solfeggio (or any) target frequency in Hz  
- `A4_src` — detected concert pitch of the recording  
- optional `preferred_pc` — pitch class 0–11 (C=0 … B=11), e.g. heart→C  
- `max_abs_cents` — safety rail (default **80 ¢**; hard fail above **100 ¢** unless user overrides)

Find MIDI note `n` in a practical singing/instrument range (default **36…96**, C2–C7):

```
A4_candidate(n) = F / 2^((n − 69) / 12)
                  = F × 2^((69 − n) / 12)
```

Score each candidate:

```
shift_cents(n) = 1200 × log2(A4_candidate(n) / A4_src)
score          = |shift_cents(n)|
```

**Selection policy (v1):**

1. If `preferred_pc` is set, restrict to `n % 12 == preferred_pc`.  
2. Among remaining, minimize `score`.  
3. Tie-break: prefer note name in mid register (MIDI 48–84), then lower `|A4_candidate − 440|`.  
4. If best `score > max_abs_cents`, widen search: drop preferred_pc and re-run (“auto degree”).  
5. Still too far → warn and offer nearest anyway, or fall back to pure A=432 / A=440 mode.

**Playback / convert ratio (always):**

```
ratio = A4_target / A4_src
```

One ratio. No key change beyond that global slide. Tempo unchanged (phase vocoder / rubber-band style pitch shift).

---

## Worked results (A4_src = 440)

Computed: best lock per Solfeggio frequency minimizing |cents from A440|.

| Solfeggio | F (Hz) | **Best lock** | **Implied A4** | Δ¢ vs 440 | Notes |
|-----------|--------|---------------|----------------|-----------|--------|
| UT 174 | 174 | **F3** | 438.45 | −6.1 | Excellent near-440 |
| UT 285 | 285 | **C♯4** | 452.41 | +48.2 | Borderline; D4 lock → A4≈427 (−52 ¢) is alt near-432 |
| UT 396 | 396 | **G4** | 444.49 | +17.6 | Strong |
| RE 417 | 417 | **G♯4** | 441.80 | +7.1 | Excellent |
| MI 528 | 528 | **C5** | **443.99** | **+15.6** | Canonical “C=528 / heart” |
| FA 639 | 639 | **D♯5** | 451.84 | +46.0 | Or E5 → A4≈426.5 (−54 ¢) |
| SOL 741 | 741 | **F♯5** | 440.60 | **+2.4** | Almost free |
| LA 852 | 852 | **G♯5** | 451.33 | +44.0 | Or A5=852 → A4=426 (−56 ¢) |
| SI 963 | 963 | **B5** | 428.97 | −44.0 | **Never A4=963** |

### Heart chakra / 528 — the Beatles case

User intent: *Octopus’s Garden → heart version with 528 on C.*

| Policy | Lock | A4 | Shift from A440 | Shift from A432 |
|--------|------|-----|-----------------|-----------------|
| **Heart / C=528 (recommended)** | C5=528 | **443.993 Hz** | **+15.6 ¢** | +47.4 ¢ from pure-432 |
| Pure Verdi/A432 | A4=432 | 432 | −31.8 ¢ | 0 |
| Naïve A=528 | A4=528 | 528 | **+315.6 ¢ (~+3.2 st)** | disaster |

Under C5=528:

- C5 = 528.000 Hz exactly  
- A4 ≈ 444.0 Hz  
- Song is still “in the same key”; it is only ~16 cents sharper than commercial A440 — often *less* movement than A432.

### “432 on A **and** 528 on C” — impossible in 12-TET

Two constraints, one degree of freedom.

| Constraint | Implies |
|------------|---------|
| A4 = 432 | C5 = 432 × 2^(3/12) ≈ **513.74 Hz** (not 528) |
| C5 = 528 | A4 = 528 / 2^(3/12) ≈ **443.99 Hz** (not 432) |

Gap between those A4s: **≈ 47.4 ¢**.  

**Product rule:** never claim both at once. Offer:

- **Mode A — Concert 432:** A4_target = 432 (or detected→432).  
- **Mode B — Solfeggio lock:** e.g. Heart → C5=528 → A4≈444.  
- **Mode C — Dual render:** export *two* library files, one per mode (jukebox can tag both).  
- **Mode D (v2, optional):** slight non-12-TET / stretch — out of scope for v1.

At A4=432, 12-TET neighbors (for UI honesty):

| Note | Hz @ A432 |
|------|-----------|
| C4 | 256.87 |
| C5 | **513.74** |
| G4 | 384.87 |
| A4 | **432.00** |

Closest Solfeggio-ish hits at pure 432: C5≈514 (near 528 but −47 ¢ flat of 528), G4≈385 (near 396 −49 ¢), etc. So “432 album” is its own aesthetic; “528 heart” is a *different* concert pitch.

---

## Chakra → default preferred pitch class (v1 map)

Defaults only — user can override lock degree in UI.

| Chakra / intent | Solfeggio F | Default lock PC | Typical best note | Typical A4 |
|-----------------|-------------|-----------------|-------------------|------------|
| Foundation | 174 | F | F3 | ~438.5 |
| Repair | 285 | C♯ or D | C♯4 / D4 | ~452 or ~427 |
| Liberation | 396 | G | G4 | ~444.5 |
| Change | 417 | G♯ | G♯4 | ~441.8 |
| **Heart** | **528** | **C** | **C5** | **~444.0** |
| Connection | 639 | D♯ or E | D♯5 / E5 | ~452 / ~426 |
| Expression | 741 | F♯ | F♯5 | ~440.6 |
| Intuition | 852 | G♯ or A | G♯5 / A5 | ~451 / 426 |
| Unity | 963 | B | B5 | ~429.0 |
| Verdi / concert | — | A | A4 | **432** exactly |

“Nice fraction of that scale” in engineering terms = **exact 12-TET membership**:  
`F = A4 × 2^((n−69)/12)` for integer `n`. That *is* the lock equation.

---

## Detected source pitch (not always 440)

Real masters sit around **439–448 Hz** historically (orchestras 442–443 common).  

Always:

```
A4_src = detect_tuning(file)   # librosa-style, cached
A4_tgt = resolve_target(mode, F, preferred_pc, A4_src)
ratio  = A4_tgt / A4_src
```

Example: song already at A=443, Heart mode wants A4=444.0 → ratio ≈ 1.0023 (**+2.3 ¢**) — nearly transparent.

Example: song at A=440, Concert-432 → ratio = 432/440 (**−31.8 ¢**).

---

## UI copy (human language, not MIDI)

Show the user:

```
Mode: Heart (528 Hz)
Lock: C5 = 528.00 Hz
Concert A: 443.99 Hz  (was 440.0 Hz)
Shift: +15.6 cents   (no key change)
```

Not: “tuning = 528 Hz” (ambiguous and wrong).

For Concert 432:

```
Mode: Concert A
Lock: A4 = 432.00 Hz
Shift: −31.8 cents from detected 440.0
C5 in this tuning: 513.74 Hz (528 is not exact — use Heart mode for C=528)
```

---

## Library dual-render naming

Non-destructive originals. Converted library examples:

```
Octopus's Garden [Concert-A432].flac
Octopus's Garden [Heart-C528_A444].flac
Octopus's Garden [Expression-F#741_A441].flac
```

Metadata tags: `A4_SRC`, `A4_TGT`, `LOCK_NOTE`, `LOCK_HZ`, `SHIFT_CENTS`, `MODE`.

---

## Pseudocode (implementation SSOT)

```python
NOTE = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

def a4_for_lock(F: float, midi_n: int) -> float:
    return F * (2 ** ((69 - midi_n) / 12.0))

def cents(a: float, b: float) -> float:
    return 1200.0 * math.log2(a / b)

def resolve_solfeggio_target(
    F: float,
    A4_src: float,
    preferred_pc: int | None = None,
    midi_lo: int = 36,
    midi_hi: int = 96,
    max_abs_cents: float = 80.0,
) -> dict:
    def candidates(pc_filter):
        out = []
        for n in range(midi_lo, midi_hi + 1):
            if pc_filter is not None and (n % 12) != pc_filter:
                continue
            a4 = a4_for_lock(F, n)
            sc = cents(a4, A4_src)
            out.append({
                "midi": n,
                "note": f"{NOTE[n % 12]}{n // 12 - 1}",
                "A4": a4,
                "shift_cents": sc,
                "score": abs(sc),
            })
        out.sort(key=lambda x: (x["score"], abs(x["midi"] - 60)))
        return out

    pool = candidates(preferred_pc)
    if not pool or pool[0]["score"] > max_abs_cents:
        pool = candidates(None)  # auto degree
    best = pool[0]
    best["ok"] = best["score"] <= max_abs_cents
    best["ratio"] = best["A4"] / A4_src
    return best

def resolve_concert_a(A4_src: float, A4_tgt: float = 432.0) -> dict:
    sc = cents(A4_tgt, A4_src)
    return {
        "midi": 69,
        "note": "A4",
        "A4": A4_tgt,
        "shift_cents": sc,
        "score": abs(sc),
        "ok": True,
        "ratio": A4_tgt / A4_src,
        "lock_hz": A4_tgt,
    }
```

---

## What is novel vs what already exists

**Exists:** 432Hz Player / Batch Converter (Hanuman Institute) — detect pitch, shift toward 432, play/convert. Audacity/DAW ratio pitch shift. librosa `estimate_tuning`.

**Convert432 addition:** treat Solfeggio as **degree-lock optimization under a cents budget**, default chakra→PC map, honest dual-mode (Concert-A vs Lock-F), dual library renders, Winamp-style jukebox that applies the chosen ratio non-destructively. The “528 on C without wrecking the Beatles” path is the product differentiator — not mysticism in the DSP.

---

## Open theory choices (product, not math)

1. **Just intonation / non-12-TET “perfect 432 + perfect 528”** — would require note-dependent stretch (impossible with one global ratio on a mixed master). Reject for mastered stereo files in v1.  
2. **Lock to song key tonic** instead of fixed C for 528 — e.g. if track is in E major, lock E to 528. Stronger “chakra of the piece” story; needs key detection. **v1.1 candidate.**  
3. **Prefer nearest to A432 rather than A_src** when user enabled “432-biased Solfeggio” — different objective function: minimize `|A4_cand − 432|` then apply ratio from A4_src. Optional preset.  
4. **Historical Verdi 432** vs **scientific C256** — at A432, C4≈256.87 (near power-of-two 256). Document as easter-egg preset `C4=256` → A4 = 256 × 2^(9/12) ≈ **430.54 Hz**.

---

## Test vectors (must pass in code)

| Input | Mode | Expected A4_tgt (approx) | |ratio − 1| band |
|-------|------|--------------------------|------------------------|
| A4_src=440, Concert 432 | concert | 432.000 | ~1.82% down |
| A4_src=440, Heart 528 | lock C | 443.993 | ~0.91% up |
| A4_src=440, Expression 741 | lock auto | 440.60 (F♯5) | ~0.14% up |
| A4_src=440, Unity 963 | lock auto | 428.97 (B5) | ~2.5% down |
| A4_src=440, Heart + force A lock | lock A=528 | 528.0 | reject or warn (>100 ¢) |
| A4_src=443, Heart 528 | lock C | 443.993 | tiny |

Formula check: `443.9933072539613 == 528 / 2**(3/12)`.

---

## Harmonic locks (octave / fifth / third) — already generalized

Exact note-lock is **partial k = 1**: some MIDI note frequency equals `F`.

**Harmonic lock** allows partial **k = 2…6**:

```
note_hz = F / k
A4 = note_hz × 2^((69 − midi) / 12)
```

Meaning in the room:

| k | Acoustic meaning | 12-TET cousin |
|---|------------------|---------------|
| 1 | The tone itself is a scale degree | unison |
| 2 | Octave below; 2nd harmonic of that note = F | octave |
| 3 | 3rd harmonic of lower note = F | ~just fifth + octave (≈702¢) |
| 4 | Two octaves below | double octave |
| 5 | 5th harmonic of lower note = F | ~just major third stack (≈386¢ class) |
| 6 | 2×3rd | fifth class again |

Constraint for “A within reason”: keep **A4 ∈ [415, 466] Hz** (roughly G♯–A♯ territory around modern pitch). Prefer |Δ¢| from detected source under 50 when possible.

Octaves (k=2,4) produce the **same A4** as k=1 for the same pitch class chain — they do not invent a new concert pitch; they only restate “C4=264 when C5=528.”  
**Odd partials (k=3,5)** *do* move A4 slightly (just vs equal tempered drift) and sometimes find a gentler A4 than k=1.

### Salient chakra presets (recommended defaults)

**Column A — 440-biased exact tone (k=1):** smallest move from commercial masters.  
**Column B — 432-biased harmonic:** A4 as close as possible to 432 while still making F a partial of some note.

| Chakra | F (Hz) | **A: default lock (k=1)** | A4 | Δ¢ vs 440 | **B: 432-friendly harmonic** | A4 | vs 432 |
|--------|--------|---------------------------|-----|-----------|------------------------------|-----|--------|
| Root (deep) | 174 | **F3 = 174** | 438.45 | −6.1 | A♯1 ×3 → 174 | 437.96 | +23.7¢ |
| Root | 396 | **G4 = 396** | 444.49 | +17.6 | (exact is better than 432-bias here) | — | — |
| Sacral | 417 | **G♯4 = 417** | 441.80 | +7.1 | C♯3 ×3 → 417 | 441.30 | +36.9¢ |
| Solar / MI heart | **528** | **C5 = 528** | **443.99** | **+15.6** | F3 ×3 → 528 | 443.49 | +13.7¢ vs 440 |
| Heart FA | 639 | D♯5 = 639 | 451.84 | +46.0 | **C3 ×5 → 639** | **429.87** | **−8.6¢** |
| Throat | 741 | **F♯5 = 741** | 440.60 | +2.4 | **B3 ×3 → 741** | **440.10** | +0.4¢ vs 440 |
| Third eye | 852 | G♯5 = 852 | 451.33 | +44.0 | **F3 ×5 → 852** | **429.38** | **−10.5¢** |
| Crown | 963 | B5 = 963 | 428.97 | −44.0 | **G3 ×5 → 963** | **432.37** | **+1.5¢** |

**Product defaults (v1 preset IDs):**

| Preset ID | Story | Mechanism |
|-----------|--------|-----------|
| `concert_432` | Verdi / classic 432 album | A4=432 exact (F not guaranteed) |
| `root_396` | Root chakra | k=1 G4=396 → A4≈444.5 |
| `sacral_417` | Sacral | k=1 G♯4=417 → A4≈441.8 |
| `heart_528` | Heart / DNA MI | k=1 **C5=528** → A4≈444.0 |
| `heart_528_fifth` | Heart, fifth-stack flavor | k=3 F3×3=528 → A4≈443.5 (almost same) |
| `heart_639_432` | Heart FA near Verdi | k=5 C3×5=639 → A4≈429.9 |
| `throat_741` | Throat | k=1 F♯5=741 → A4≈440.6 (almost free) |
| `throat_741_fifth` | Throat, ~pure A440 | k=3 B3×3=741 → A4≈440.1 |
| `third_eye_852_432` | Ajna near 432 | k=5 F3×5=852 → A4≈429.4 |
| `crown_963_432` | Crown ≈ stays on 432 | k=5 G3×5=963 → A4≈432.4 |
| `foundation_174` | Deep root | k=1 F3=174 → A4≈438.5 |

### Fixed A4=432: how close do magic tones get?

You cannot hit every Solfeggio exactly at pure 432. Best partial approaches:

| F | Closest at A432 | Error |
|---|-----------------|-------|
| 174 | A♯1×3 ≈ 171.6 | −24¢ |
| 285 | A♯1×5 ≈ 286.1 | **+6¢** (excellent) |
| 396 | E2×5 ≈ 404.5 | +37¢ |
| 417 | C♯2×6 ≈ 408.2 | −37¢ |
| 528 | A2×5 = 540 | +39¢ (not great — use Heart mode instead) |
| 639 | C3×5 ≈ 642.2 | **+9¢** (good) |
| 741 | B2×6 ≈ 727.4 | −32¢ |
| 852 | F3×5 ≈ 857.2 | **+11¢** (good) |
| 963 | G3×5 ≈ 962.2 | **−1.5¢** (essentially exact) |

So a **pure Concert-432 playlist** already “contains” crown 963 and is close on 639/852/285 as harmonics — marketing can say that honestly — while **528 heart still wants its own ~A444 render**.

### Fixed A4≈444 (Heart C528 world) — bonus stack

When C5=528 exactly, other partials fall out:

| F | Hit | Error |
|---|-----|-------|
| 528 | C5 (or C4×2, C3×4) | **exact** |
| 396 | C2×6 | **exact** |
| 741 | D3×5 | **−0.4¢** |
| 417 | E2×5 | −5.1¢ |

Heart mode is a **small constellation**: 528 + 396 + ~741 tag along. Document in UI as “Heart constellation (C528).”

### Resolver extension (v1.1 math, optional v0.3)

```text
resolve_lock(F, a4_src, preferred_pc=None, allowed_k=(1,2,3,4,5,6),
             a4_band=(415,466), bias='source'|'432'|'440')
```

- Enumerate midi × k  
- Filter A4 in band  
- Score = |cents(A4, bias_ref)| + small penalty × (k−1)  // prefer audible fundamentals  
- Return best  

v1 ships **k=1 only** (simpler UX). Preset table above hard-codes the best k=3/k=5 rows as named presets so harmonic options appear without exposing “partial k” to casual users.

---

## Worlds, extended palette, sub-audio (2026-09-11)

Code SSOT: `tools/palette.py` + `tools/resolve_target.py`. ADR: `docs/adr/002-worlds-and-modulation.md`.

**A=444 is the solfeggio world, not a new DSP.** `heart_528` already produces A4≈443.993. Census: 11/34 market tones sit on 12-TET degrees at A=444 vs 2/34 at A=432. Angel/numeric 111/222/444/888 are the same grid (111×4=444 exactly). Concert-A product default stays Verdi 432 — a real, thinner world that owns OM 136.10 Hz and 1152 Hz.

**`resolve_target()` audio floor = 60 Hz.** Below that, raise. Do not lock 7.83 → A4≈52.67. Role on each palette row: `degree-lock | modulation-rate | physical-vibration`. 40 Hz is all three; the façade still raises.

**Modulation plan** (`resolve_modulation`): binaural pair (headphone-only) and isochronic gate of a *standalone tone* are the public-domain side. Music-AM (tremolo on the mixed track) is recorded as physics (sidebands f±R) with `ship=false` pending FTO (Brain.fm US7674224B2 + 2025 continuations). Play/Convert refuse a fake A4.

**Corrections baked in:** 194.18 Hz = solar day (86,400 s); sidereal = 194.71 Hz. Do not label 111 Hz “Hypogeum resonance” (Hal Saflieni 70/114 Hz; 110–112 Hz is Jahn 1995 survey). Only Schumann f1≈7.83 Hz is a stable figure. No Rife disease lists. Do not cite “Verdiyev 2019”.

**Handoff lock vectors** (A4_src=440, k=1):

| F (Hz) | lock | A4 | notes |
|--------|------|----|-------|
| 111 | A2 | 444.000 | exact |
| 888 | A5 | 444.000 | exact |
| 136.10 | C#3 | 432.09 | OM / Earth-year |
| 172.06 | F3 | 433.56 | platonic year |
| 194.18 | G3 | 435.92 | solar day |
| 2172 | C7 | 456.61 | edge (~+64¢), not rejected |
| 40 | — | raise | modulation |
| 7.83 | — | raise | modulation |

