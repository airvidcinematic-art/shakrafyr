"""SHAKRA-FYER frequency palette — worlds, families, roles.

SSOT for lock tones beyond the original solfeggio set. DSP does not live here:
src-tauri/src/bridge.rs handles the bridge from these labels to the audio engine.

Lock identity:
  C5=528 → A4. Exact identity used by heart_528 / world_444.
  A440 is ISO 16 default, the modern standard, not a tuning philosophy.

RIFE_BLOCKLIST_HZ: consumer Rife lists pair these with named diseases. Never ship
as presets. This is a blocklist, not a catalogue — the diseases are somebody
else's to name.
"""

from dataclasses import dataclass, field
from typing import Literal

# --- Role taxonomy ---------------------------------------------------------
# degree-lock   = a frequency that anchors a scale degree (A4 solves from it)
# modulation-rate = a Hz rate, not a scale degree — modulation mode only
# physical-vibration = a measured physical phenomenon (Schumann, etc.)

ROLES = ("degree-lock", "modulation-rate", "physical-vibration")


@dataclass(frozen=True)
class Tone:
    id: str
    freq_hz: float
    family: str
    label: str
    short: str
    desc: str
    evidence_tier: str
    world: str | None = None
    midi: int | None = None
    preferred_pc: int | None = None
    roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class World:
    id: str
    a4: float
    label: str
    desc: str


WORLD_444 = World(
    id="world_444", a4=443.9933072539613,
    label="Solfeggio world · A≈444",
    desc="Native grid for solfeggio + numeric tones. Heart C5=528 already produces this A4.",
)
WORLD_432 = World(
    id="world_432", a4=432.0,
    label="Cosmic world · A=432",
    desc="Owns Cousto OM 136.10 and 1152 Hz. A real world, thinner for solfeggio (528 sits +47.4¢ off).",
)
WORLD_440 = World(
    id="world_440", a4=440.0,
    label="ISO standard · A=440",
    desc="The international recommendation. Settled in 1939. The world most production tools live in.",
)

# heart_528 locks C5=528. Concert A4 solves from C5. This is the identity.
HEART_A4 = 443.9933072539613

# --- Concert-A ids the façade accepts. heart_528 stays a lock preset (library names). --
CONCERT_A_IDS = {
    "concert_432": ("world_432", 432.0),
    "verdi_432": ("world_432", 432.0),
    "world_432": ("world_432", 432.0),
    "world_444": ("world_444", HEART_A4),
    "world_440": ("world_440", 440.0),
    "iso_440": ("world_440", 440.0),
}

# --- DSP constants (consumed by resolve_target, tests, bridge) ----------
AUDIO_FLOOR_HZ = 60.0
EDGE_CENTS = 20.0
RAIL_CENTS = 80.0

# --- World catalogue -----------------------------------------------------
WORLDS = {
    w.id: w for w in (WORLD_444, WORLD_432, WORLD_440)
}

# --- Concert-A ids the façade accepts. heart_528 stays a lock preset. --
CONCERT_IDS = CONCERT_A_IDS = {
    "concert_432": ("world_432", 432.0),
    "verdi_432": ("world_432", 432.0),
    "world_432": ("world_432", 432.0),
    "world_444": ("world_444", HEART_A4),
    "world_440": ("world_440", 440.0),
    "iso_440": ("world_440", 440.0),
}

RIFE_BLOCKLIST_HZ = frozenset({727, 787, 880})
"""Consumer Rife lists pair these with named diseases. Never ship as presets.
The diseases are somebody else's to name — we just know the frequencies.
"""


def _t(
    id: str,
    freq_hz: float,
    family: str,
    label: str,
    short: str,
    desc: str,
    evidence_tier: str = "tradition",
    world: str | None = None,
    midi: int | None = None,
    preferred_pc: int | None = None,
    roles: tuple[str, ...] = (),
) -> Tone:
    return Tone(
        id=id, freq_hz=freq_hz, family=family, label=label, short=short,
        desc=desc, evidence_tier=evidence_tier, world=world, midi=midi,
        preferred_pc=preferred_pc, roles=roles,
    )


# --- Extended sets (higher octave, edge-of-rail) -----------------
# "extended_set" keeps the test assertion consistent.
_extended_family = "extended_set"

PALETTE: tuple[Tone, ...] = (
    # --- Solfeggio (k=1). heart_528 is the solfeggio-world default lock. ---
    _t("foundation_174", 174.0, "solfeggio", "Foundation · F = 174 Hz", "Found 174",
       "Solfeggio UT-adjacent foundation tone. F3 locks to 174 Hz. The earth register — canopy as shelter, not as sky.",
       preferred_pc=5, midi=53),
    _t("repair_285", 285.0, "solfeggio", "Repair · C♯ = 285 Hz", "Repair 285",
       "Quarter-tone group (~+48¢ from A440). Lock note + concert A, never a bare 285 label.",
       preferred_pc=1, midi=61),
    _t("root_396", 396.0, "solfeggio", "Root · G = 396 Hz", "Root 396",
       "Solfeggio UT — grounding / home. G4 locks to 396 Hz (concert A ≈ 444.5). Traditional paradigm says good for bladder.",
       world="world_444", preferred_pc=7, midi=67),
    _t("sacral_417", 417.0, "solfeggio", "Sacral · G♯ = 417 Hz", "Sacral 417",
       "Solfeggio RE — change / unsticking a pattern. G♯4 locks to 417 Hz.",
       preferred_pc=8, midi=68),
    _t("heart_528", 528.0, "solfeggio", "Heart · C = 528 Hz", "Heart C528",
       "Solfeggio MI. C5=528 is the solfeggio world (A≈444). Legends say it clears the skin. We lock C5 to 528 Hz (concert A ≈ 444, about +16 ¢). A gentle retune — never A4=528, which would transpose the song by three semitones.",
       evidence_tier="small_study", world="world_444", preferred_pc=0, midi=72),
    _t("heart_639", 639.0, "solfeggio", "Anahata · D♯ = 639 Hz", "Heart 639",
       "7-set heart chakra is 639, not 528. D♯5 lock; ~+46¢ — edge of the retune band.",
       preferred_pc=10, midi=75),
    _t("throat_741", 741.0, "solfeggio", "Throat · F♯ = 741 Hz", "Throat 741",
       "Solfeggio SOL — expression. F♯5=741, concert A almost 440.",
       preferred_pc=6, midi=78),
    _t("third_eye_852", 852.0, "solfeggio", "Third eye · G♯ = 852 Hz", "Ajna 852",
       "Solfeggio LA. G♯5 lock sits in the quarter-tone group (~+44¢).",
       preferred_pc=8, midi=80),
    _t("crown_963", 963.0, "solfeggio", "Crown · B = 963 Hz", "Crown 963",
       "Solfeggio SI — unity. B5 lock. At A=432 the 5th harmonic of G3 is ~−1.5¢.",
       preferred_pc=11, midi=83),
    # --- Cosmic Octave (Cousto). All k=1 inside the ±80¢ rail. ---
    _t("sun_126", 126.22, "cosmic_octave", "Sun · 126.22 Hz", "Sun 126",
       "Cousto solar tone. Puts this period on a 12-TET degree; no outcome claim.",
       evidence_tier="physics", preferred_pc=7, midi=47),
    _t("om_136", 136.10, "cosmic_octave", "OM / Earth-year · 136.10 Hz", "OM 136",
       "Cousto Earth-year tone. Exact on the A=432 grid (C♯3). Physics of a period, not a medical claim.",
       evidence_tier="physics", world="world_432", preferred_pc=1, midi=49),
    _t("throat_141", 141.27, "cosmic_octave", "Mercury · 141.27 Hz", "Mercury 141",
       "Cousto Mercury tone (throat mapping in that tradition).",
       evidence_tier="physics", preferred_pc=6, midi=49),
    _t("mars_144", 144.72, "cosmic_octave", "Mars · 144.72 Hz", "Mars 144",
       "Cousto Mars tone.", evidence_tier="physics", preferred_pc=0, midi=50),
    _t("saturn_147", 147.85, "cosmic_octave", "Saturn · 147.85 Hz", "Saturn 147",
       "Cousto Saturn. Lands on the A≈444 grid.",
       evidence_tier="physics", world="world_444", preferred_pc=8, midi=50),
    _t("crown_172", 172.06, "cosmic_octave", "Platonic year · 172.06 Hz", "Crown 172",
       "Cousto platonic-year tone. Sits between the 432 and 444 worlds.",
       evidence_tier="physics", preferred_pc=6, midi=53),
    _t("jupiter_183", 183.58, "cosmic_octave", "Jupiter · 183.58 Hz", "Jupiter 183",
       "Cousto Jupiter tone.", evidence_tier="physics", preferred_pc=3, midi=54),
    _t("root_194", 194.18, "cosmic_octave", "Solar day · 194.18 Hz", "Solar 194",
       "Cousto solar-day tone (86,400 s). Not the sidereal day — that is 194.71 Hz.",
       evidence_tier="physics", preferred_pc=7, midi=55),
    _t("sidereal_194", 194.71, "cosmic_octave", "Sidereal day · 194.71 Hz", "Sidereal 194",
       "Cousto sidereal-day tone. Distinct from solar day 194.18 Hz.",
       evidence_tier="physics", preferred_pc=7, midi=55),
    _t("sacral_210", 210.42, "cosmic_octave", "Moon · 210.42 Hz", "Moon 210",
       "Cousto synodic-month tone.", evidence_tier="physics", preferred_pc=8, midi=56),
    _t("third_eye_221", 221.23, "cosmic_octave", "Venus · 221.23 Hz", "Venus 221",
       "Cousto Venus tone.", evidence_tier="physics", preferred_pc=9, midi=57),
    # --- archaeoacoustics ---
    _t("newgrange_110", 110.0, "archaeoacoustics", "Newgrange · 110 Hz", "Newgrange 110",
       "Measured chamber resonance. A2=110 at modern A=440 — exact degree, physics tier.",
       evidence_tier="physics", world="world_440", preferred_pc=5, midi=45),
    _t("hypogeum_111", 111.0, "archaeoacoustics", "111 Hz · megalithic survey", "111 Hz",
       "111 Hz is A2 on the A=444 grid (111×4=444). The 110–112 Hz figure is from a wider megalithic survey, not the Hal Saflieni double resonance (70 / 114 Hz). Same render as numeric 111 Hz.",
       evidence_tier="physics", world="world_444", preferred_pc=5, midi=45),
    # --- instrument / scientific pitch ---
    _t("fork_128", 128.0, "instrument", "Otto fork · C = 128 Hz", "Fork 128",
       "C3=128 scientific-ish fork. Implies A4≈430.54 (same world as C4=256).",
       evidence_tier="physics", preferred_pc=0, midi=48),
    _t("c256", 256.0, "instrument", "Scientific C4 = 256 Hz", "C256",
       "Power-of-two middle C. A4 = 256 × 2^(9/12) ≈ 430.54 Hz.",
       evidence_tier="physics", preferred_pc=0, midi=60),
    # --- numeric locks (Hz labels only; 111×4=444 is arithmetic, not a doctrine) ---
    _t("num_111", 111.0, "numeric_lock", "111 Hz", "111 Hz",
       "A2=111 Hz. Same grid as A=444 (111×4=444). Number label only.",
       evidence_tier="physics", world="world_444", preferred_pc=5, midi=45),
    _t("num_222", 222.0, "numeric_lock", "222 Hz", "222 Hz",
       "A3=222 Hz. Octave of 111; same A=444 grid.",
       evidence_tier="physics", world="world_444", preferred_pc=5, midi=57),
    _t("num_333", 333.0, "numeric_lock", "333 Hz", "333 Hz",
       "E4≈333 Hz on the A≈444 grid. Number label only.",
       world="world_444", preferred_pc=1, midi=64),
    _t("num_444", 444.0, "numeric_lock", "444 Hz", "444 Hz",
       "A4=444 Hz exactly. Concert pitch of the solfeggio world, as a numbered lock.",
       evidence_tier="physics", world="world_444", preferred_pc=1, midi=69),
    _t("num_555", 555.0, "numeric_lock", "555 Hz", "555 Hz",
       "C♯5≈555 Hz, near modern A=440. Number label only.",
       evidence_tier="physics", world="world_444", preferred_pc=1, midi=57),
    _t("num_666", 666.0, "numeric_lock", "666 Hz", "666 Hz",
       "E5≈666 Hz on the A≈444 grid. Number label only.",
       evidence_tier="physics", world="world_444", preferred_pc=1, midi=76),
    _t("num_777", 777.0, "numeric_lock", "777 Hz", "777 Hz",
       "G5≈777 Hz. Number label only.",
       evidence_tier="physics", world="world_444", preferred_pc=1, midi=79),
    _t("num_888", 888.0, "numeric_lock", "888 Hz", "888 Hz",
       "A5=888 Hz. Two octaves above 222; A=444 grid. Number label only.",
       evidence_tier="physics", world="world_444", preferred_pc=1, midi=81),
    _t("num_999", 999.0, "numeric_lock", "999 Hz", "999 Hz",
       "B5≈999 Hz. Number label only.",
       evidence_tier="physics", world="world_444", preferred_pc=1, midi=83),
    # --- extended sets (higher octave, edge-of-rail) ---
    _t("ext_1074", 1074.0, "extended_set", "1074 Hz", "1074 Hz",
       "Extended-set C6 lock. Number label only.", preferred_pc=0, midi=84),
    _t("ext_1152", 1152.0, "extended_set", "1152 Hz", "1152 Hz",
       "Lands on the A=432 world. Number label only.", preferred_pc=0, midi=86),
    _t("ext_1174", 1174.0, "extended_set", "1174 Hz", "1174 Hz",
       "D6 lock, nearly A=440. Number label only.", preferred_pc=1, midi=86),
    _t("ext_2172", 2172.0, "extended_set", "2172 Hz", "2172 Hz",
       "C7 lock. Edge of the ±80¢ rail (~+64¢) — warn, do not reject.", preferred_pc=0, midi=96),
)

# --- Modulation-rate tones (geophysical, not scale degrees) ---
MODULATION_PRESETS: tuple[Tone, ...] = (
    _t("delta_2", 2.0, "geophysical", "Delta · 2 Hz", "Delta 2",
       "Delta-band rate. Not a scale degree — modulation mode only.",
       roles=("modulation-rate",), evidence_tier="measured_not_audible"),
    _t("theta_6", 6.0, "geophysical", "Theta · 6 Hz", "Theta 6",
       "Theta-band rate. Not a scale degree — modulation mode only.",
       roles=("modulation-rate",), evidence_tier="measured_not_audible"),
    _t("schumann_7_83", 7.83, "geophysical", "Schumann · 7.83 Hz", "Schumann 7.83",
       "Earth-ionosphere resonance, used as a rhythm. Not sound in air at 7.83 Hz.",
       roles=("modulation-rate",), evidence_tier="measured_not_audible"),
    _t("alpha_10", 10.0, "geophysical", "Alpha · 10 Hz", "Alpha 10",
       "Alpha-band rate. Not a scale degree — modulation mode only.",
       roles=("modulation-rate",), evidence_tier="measured_not_audible"),
    _t("smr_13", 13.0, "geophysical", "SMR · 13 Hz", "SMR 13",
       "Sensorimotor-rhythm rate. Not a scale degree — modulation mode only.",
       roles=("modulation-rate",), evidence_tier="measured_not_audible"),
    _t("beta_18", 18.0, "geophysical", "Beta · 18 Hz", "Beta 18",
       "Beta-band rate. Not a scale degree — modulation mode only.",
       roles=("modulation-rate",), evidence_tier="measured_not_audible"),
    _t("gamma_40", 40.0, "geophysical", "Gamma · 40 Hz", "Gamma 40",
       "40 Hz is three products: a rate, a sub-bass tone, and a vibration band. Default path is modulation — never silently emit an A4.",
       roles=("degree-lock", "modulation-rate", "physical-vibration"),
       evidence_tier="small_study"),
)

# --- Bypass ---
BYPASS_PRESETS = (
    _t("bypass", 0.0, "bypass", "Bypass", "Bypass",
       "Original pitch · no shift applied. A4_src stays as-is; no retune.",
       midi=None),
)

def get_tone(tone_id: str) -> Tone | None:
    """Lookup a Tone by id, or None. Searches PALETTE, MODULATION_PRESETS, and BYPASS_PRESETS."""
    for _pool in (PALETTE, MODULATION_PRESETS, BYPASS_PRESETS):
        for t in _pool:
            if t.id == tone_id:
                return t
    return None


# --- Bridge metadata ---
BRIDGE_NOTE = (
    "Modulation is a rate — Play will not invent an A4. Music-AM on the track "
    "is off pending FTO. Binaural / isochronic apply to a generated tone, not "
    "the mix. Headphones for binaural."
)

PLAY_PRESETS_HINT = (
    "Historical orchestra A4 targets plus the solfeggio world (A≈444). "
    "Default stays Verdi 432."
)

MODULATION_HINT = (
    "Rates, not scale degrees. Play/Convert refuse a fake A4. "
    "Binaural is headphone-only."
)

LOCK_HINT = (
    "Locks a frequency onto a scale degree. A4 is solved from that lock — "
    "not forced equal to F. Families are tabs, not one dump row."
)
