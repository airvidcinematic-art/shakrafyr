# Convert432 Theme Reference — “Neon Glass Jukebox”

**Status:** Binding visual SSOT for UI work  
**Inspiration asset:** [`references/theme-ref-jukebox-dark.png`](references/theme-ref-jukebox-dark.png) (Fastpotify-style mock: player + EQ + playlist)  
**Aesthetic keywords:** cyberpunk · synthwave · glassmorphism · neon noir · retro-futurist HUD · Winamp *structure* with 2020s neon *skin*

Winamp is the **information architecture** (stacked player / EQ / playlist). This image is the **paint**.

---

## Layout (three stacked panels)

| Panel | Role | Convert432 mapping |
|-------|------|-------------------|
| **Top — Player** | Brand, cassette/glyph, big time, track title, bitrate/meta, scrubber, transport, SHUFFLE/REP | Main transport + **tuning readout** (A4 src→tgt, lock note, ¢) |
| **Middle — Equalizer** | Waveform + 10-band faders + ON/AUTO | Spectrum + optional EQ; **or** RE-Tune module surface (bands as “lock strength” is YAGNI — keep real EQ) |
| **Bottom — Playlist** | Numbered tracks, durations, ADD/REM/SEL/MISC, LIST OPTS | Library / queue; badges for preset (`432`, `C528`, etc.) |

Panels float over a **deep void** background (subtle grid / noise). Gaps between panels ~12px. Each panel is a frosted glass card with neon edge.

**RE-Tune module:** own panel or tab adjacent to EQ — see plan note. Visually same glass language; content = mode picker, lock readout, cents meter, Apply.

---

## Color tokens

```css
:root {
  /* voids */
  --c432-bg-deep: #05000a;
  --c432-bg-grid: #0a0015;
  --c432-bg-panel: rgba(20, 5, 40, 0.65);
  --c432-bg-panel-solid: #140528;

  /* neon primaries */
  --c432-cyan: #00f3ff;
  --c432-cyan-dim: rgba(0, 243, 255, 0.35);
  --c432-cyan-glow: rgba(0, 243, 255, 0.6);
  --c432-magenta: #bd00ff;
  --c432-magenta-dim: rgba(189, 0, 255, 0.45);
  --c432-magenta-glow: rgba(189, 0, 255, 0.5);

  /* text */
  --c432-text: #ffffff;
  --c432-text-secondary: #e0e0e0;
  --c432-text-dim: #8a7fa8;
  --c432-text-lcd: #00f3ff; /* time + active nums */

  /* borders / hairlines */
  --c432-border: rgba(0, 243, 255, 0.35);
  --c432-border-strong: #00f3ff;
  --c432-border-magenta: rgba(189, 0, 255, 0.4);

  /* semantic (Convert432-specific) */
  --c432-ok: #00f3ff;       /* shift within rail */
  --c432-warn: #ffcc00;     /* |¢| > 50 */
  --c432-danger: #ff2a6d;   /* |¢| > 80 / blocked */
  --c432-bypass: #8a7fa8;   /* original / no shift */
}
```

**Usage rule:** Cyan = primary controls, active track numbers, filled sliders, time. Magenta = waveform, secondary glow, hover accents. Never pure gray chrome — always purple-void undertone.

---

**Typography**

```css
--c432-font: 'Azo Sans', 'AzoSans', system-ui, sans-serif;
/* display / body / LCD all use Azo Sans (single family) */
```

Weights: Thin 100 · Light 300 · Regular 400 · Medium 500 · Bold 700.  
Mockup loads local TTFs from `docs/sketches/neon-glass-v1/fonts/`.

---

## Effects

```css
:root {
  --c432-radius: 4px;           /* slightly soft; mock uses near-sharp + chamfer feel */
  --c432-radius-btn: 2px;
  --c432-blur: 12px;
  --c432-panel-shadow: 0 0 24px rgba(189, 0, 255, 0.15), inset 0 0 40px rgba(0, 0, 0, 0.35);
  --c432-neon-cyan: 0 0 6px var(--c432-cyan-glow), 0 0 14px rgba(0, 243, 255, 0.35);
  --c432-neon-magenta: 0 0 6px var(--c432-magenta-glow), 0 0 16px rgba(189, 0, 255, 0.3);
  --c432-panel-border: 1px solid var(--c432-border);
}
```

- **Glass:** `background: var(--c432-bg-panel); backdrop-filter: blur(var(--c432-blur));`  
- **Panel edge:** thin cyan border + soft magenta outer glow.  
- **Active control:** cyan fill or cyan border + `box-shadow: var(--c432-neon-cyan)`.  
- **Waveform:** magenta stroke, slight glow.  
- **No** skeuomorphic brushed metal; no flat Material gray.

---

## Components

### Panel chrome
- Title strip left or top: glyph (cassette / tuning fork) + wordmark `CONVERT432` or short `C432`.  
- Optional right meta: sample rate / bitrate / **detected A4**.

### Transport
- Row of square-ish icon buttons (prev / play / pause / stop / next).  
- Play = circular hit target OK (as in mock).  
- SHUFFLE / REP = outlined text chips; active = cyan fill or cyan border glow.

### Scrubber
- Track: dim purple line.  
- Elapsed: cyan.  
- Thumb: small glowing cyan rect/circle.

### EQ / visualizer
- 8–10 vertical faders; track dark, fill cyan gradient bottom→top.  
- Knob: small square, cyan glow.  
- ON / AUTO: pill or rect toggles.

### Playlist row
```
[##]  Title........................  m:ss
```
- Index cyan, title white, duration cyan right-aligned.  
- Selected row: magenta/cyan left bar or full-row dim fill.  
- Optional badge pill: `432` · `C528` · `741` · `ORIG`.

### Buttons (ADD REM SEL MISC)
- Transparent bg, 1px cyan border, uppercase mono label, tight padding.  
- Hover: bg `rgba(0,243,255,0.15)` + glow.  
- Active: solid cyan, dark text.

### RE-Tune module (new)
Same panel chrome. Internal layout:

```
┌ RE-TUNE ─────────────────────────┐
│ Mode: [Concert A ▾] [Solfeggio ▾]│
│ Preset chips: 432  Heart  Throat…│
│ LCD: Lock C5=528 · A 443.99 · +16¢│
│ Cents bar: |----•----|  (cyan)   │
│ [Preview A/B] [Apply to Play]    │
│ [Queue Convert…]                 │
└──────────────────────────────────┘
```

- Mode segmented control = SHUFFLE-style chips.  
- Cents bar: center = 0; warn/danger colors past rails (50 / 80).  
- Never show lone “528 Hz” without lock note + A4.

---

## Density & motion

- Compact: player height ~120–140px content; EQ ~160px; playlist flex.  
- Prefer **one column stack** on default window (classic Winamp); optional side-by-side on wide.  
- Motion: soft glow pulse on play (≤0.5Hz); waveform 30–60fps; no bouncy Material transitions.  
- Scrollbars: thin, cyan thumb, transparent track.

---

## Do / Don’t

| Do | Don’t |
|----|-------|
| Cyan primary, magenta energy | Bootstrap blue / gray flat |
| Uppercase micro-labels | Sentence-case Material headers |
| Glass panels on void | White content cards |
| Honest tuning LCD | Vague “432 mode” only |
| Pixel/simple transport icons | Oversized iOS SF Symbols |
| Sharp-ish corners (2–4px) | 16px pill-everything |

---

## Implementation mapping

| Token file | Path (when app exists) |
|------------|------------------------|
| CSS variables | `src/styles/tokens.css` |
| Global skin | `src/styles/c432-theme.css` |
| Panel primitives | `src/components/chrome/GlassPanel.tsx` |
| This reference | `docs/design/theme-neon-glass-jukebox.md` |
| PNG | `docs/design/references/theme-ref-jukebox-dark.png` |

Frontend tasks must import tokens — no one-off hex in components unless semantic override.

---

## Attribution

Reference mock labeled **FASTPOTIFY** in-frame (third-party style inspiration only). Convert432 wordmark/branding replaces it; do not ship their logo or name.
