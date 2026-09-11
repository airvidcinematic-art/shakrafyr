"""Resolve A4_target from a mode / lock frequency / palette id.

Single DSP primitive for pitch: ratio = A4_target / A4_src.
Sub-audio rates (< 60 Hz) must not go through this façade — they are
modulation-rate (or vibration) products, not scale degrees.
"""
from __future__ import annotations

import math

from tools.palette import (
    AUDIO_FLOOR_HZ,
    CONCERT_IDS,
    EDGE_CENTS,
    RAIL_CENTS,
    BYPASS_PRESETS,
    MODULATION_PRESETS,
    get_tone,
)

NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class SubAudioTargetError(ValueError):
    """F below the audio floor is a rate, not a 12-TET degree."""

    def __init__(self, f_hz: float):
        self.f_hz = f_hz
        super().__init__(
            f"{f_hz:g} Hz is below the {AUDIO_FLOOR_HZ:g} Hz audio floor — "
            "use resolve_modulation() (rate), not a scale-degree lock"
        )


def note_name(midi: int) -> str:
    return f"{NOTE[midi % 12]}{midi // 12 - 1}"


def a4_for_lock(f_hz: float, midi_n: int) -> float:
    return f_hz * (2.0 ** ((69 - midi_n) / 12.0))


def cents(a: float, b: float) -> float:
    return 1200.0 * math.log2(a / b)


def band_of(shift_cents: float) -> str:
    a = abs(shift_cents)
    if a <= EDGE_CENTS:
        return "yes"
    if a <= RAIL_CENTS:
        return "edge"
    return "NO"


def _result(
    *,
    mode: str,
    a4_src: float,
    a4_target: float,
    lock: str,
    role: str = "degree-lock",
    world: str | None = None,
    lock_midi: int | None = None,
    f_hz: float | None = None,
    preset_id: str | None = None,
    ok: bool = True,
) -> dict:
    shift = cents(a4_target, a4_src)
    return {
        "mode": mode,
        "a4_target": a4_target,
        "ratio": a4_target / a4_src,
        "shift_cents": shift,
        "lock": lock,
        "lock_midi": lock_midi,
        "lock_note": note_name(lock_midi) if lock_midi is not None else None,
        "role": role,
        "world": world,
        "band": band_of(shift),
        "ok": ok,
        "f_hz": f_hz,
        "preset_id": preset_id,
    }


def resolve_lock(
    f_hz: float,
    a4_src: float,
    *,
    preferred_pc: int | None = None,
    midi_lo: int = 36,
    midi_hi: int = 96,
    max_abs_cents: float = RAIL_CENTS,
) -> dict:
    """k=1 optimal degree lock. Caller must already have passed the audio floor."""

    def candidates(pc_filter: int | None) -> list[dict]:
        out: list[dict] = []
        for n in range(midi_lo, midi_hi + 1):
            if pc_filter is not None and (n % 12) != pc_filter:
                continue
            a4 = a4_for_lock(f_hz, n)
            sc = cents(a4, a4_src)
            out.append(
                {
                    "midi": n,
                    "note": note_name(n),
                    "a4": a4,
                    "shift_cents": sc,
                    "score": abs(sc),
                }
            )
        out.sort(key=lambda x: (x["score"], abs(x["midi"] - 60)))
        return out

    pool = candidates(preferred_pc)
    if not pool or pool[0]["score"] > max_abs_cents:
        pool = candidates(None)
    if not pool:
        raise ValueError(f"no MIDI candidate for {f_hz:g} Hz in {midi_lo}–{midi_hi}")
    best = pool[0]
    return best


# Brain.fm family (US7674224B2 + 2025 continuations) covers entrainment
# carried by modulating *musical elements*. Tone-gating / binaural beats on a
# generated tone are the public-domain side. Music-AM stays planned until FTO.
MUSIC_AM_FTO_NOTE = (
    "music-AM disabled pending FTO — Brain.fm US7674224B2 / US11966661 / "
    "US12190017 / US12406651 / US12436729 (modulating musical elements to "
    "carry entrainment). Generic binaural / isochronic *tone* generation is clear."
)


def resolve_modulation(
    rate_hz: float,
    *,
    carrier_hz: float = 528.0,
    binaural_carrier: float = 200.0,
    audible_lo: float = 20.0,
) -> dict:
    """Plan for a sub-audio rate. Never returns an A4_target.

    Shippable now: binaural pair + isochronic gate of a *standalone tone*,
    plus Cousto octave-lift of the rate into an audible drone tone.
    Not shippable without FTO: amplitude-modulating the mixed music bus.
    """
    n = 0
    lifted = float(rate_hz)
    while lifted < audible_lo:
        lifted *= 2.0
        n += 1
    lower = float(carrier_hz) - float(rate_hz)
    upper = float(carrier_hz) + float(rate_hz)
    return {
        "mode": "modulation_rate",
        "rate_hz": float(rate_hz),
        "role": "modulation-rate",
        "binaural": {
            "left_hz": float(binaural_carrier),
            "right_hz": float(binaural_carrier) + float(rate_hz),
            "headphone_only": True,
            "ship": True,
        },
        "tone_gate": {
            "carrier_hz": float(carrier_hz),
            "rate_hz": float(rate_hz),
            "kind": "isochronic",
            "on": "standalone_tone",
            "ship": True,
        },
        "music_am": {
            "ship": False,
            "flag": "music_am_disabled",
            "carrier_is": "music",
            "sidebands": {"lower": lower, "upper": upper},
            "note": MUSIC_AM_FTO_NOTE,
        },
        "octave_lift": {"n": n, "hz": lifted, "floor_hz": audible_lo, "ship": True},
    }


def resolve_target(
    *,
    a4_src: float,
    mode: str | None = None,
    f_hz: float | None = None,
    a4_tgt: float | None = None,
    preferred_pc: int | None = None,
    preset_id: str | None = None,
    midi_lo: int = 36,
    midi_hi: int = 96,
    max_abs_cents: float = RAIL_CENTS,
) -> dict:
    """Façade: concert_a / solfeggio_lock / bypass → A4_target.

    Raises SubAudioTargetError for F < 60 Hz (incl. 7.83 and 40).
    Raises ValueError if asked to treat modulation_rate as a pitch ratio.
    """
    if mode == "modulation_rate":
        raise ValueError(
            "modulation_rate is not a pitch-ratio mode — call resolve_modulation()"
        )

    if preset_id and preset_id not in CONCERT_IDS and preset_id != "bypass":
        if get_tone(preset_id) is None and not any(t.id == preset_id for t in MODULATION_PRESETS + BYPASS_PRESETS):
            raise ValueError(f"unknown preset {preset_id!r}")

    if preset_id == "bypass" or mode == "bypass":
        return _result(
            mode="bypass",
            a4_src=a4_src,
            a4_target=a4_src,
            lock="Original",
            role="degree-lock",
            preset_id=preset_id or "bypass",
        )

    if preset_id and preset_id in CONCERT_IDS:
        world_id, concert_a4 = CONCERT_IDS[preset_id]
        tgt = float(a4_tgt) if a4_tgt is not None else float(concert_a4)
        return _result(
            mode="concert_a",
            a4_src=a4_src,
            a4_target=tgt,
            lock=f"A4={tgt:.3f}",
            world=world_id,
            lock_midi=69,
            preset_id=preset_id,
        )

    tone = get_tone(preset_id) if preset_id else None
    modulation_preset = None
    if preset_id:
        for _mp in MODULATION_PRESETS:
            if _mp.id == preset_id:
                modulation_preset = _mp
                break
    if tone is not None:
        f_hz = tone.freq_hz
        if preferred_pc is None:
            preferred_pc = tone.preferred_pc
        if not mode:
            mode = "solfeggio_lock"
    elif modulation_preset is not None:
        f_hz = modulation_preset.freq_hz
        if not mode:
            mode = "modulation_rate"

    if mode == "concert_a":
        if a4_tgt is None:
            raise ValueError("concert_a requires a4_tgt or a concert preset_id")
        return _result(
            mode="concert_a",
            a4_src=a4_src,
            a4_target=float(a4_tgt),
            lock=f"A4={float(a4_tgt):.3f}",
            lock_midi=69,
            preset_id=preset_id,
        )

    if f_hz is None:
        raise ValueError("solfeggio_lock requires f_hz or a lock preset_id")

    if f_hz < AUDIO_FLOOR_HZ:
        raise SubAudioTargetError(f_hz)

    mode = mode or "solfeggio_lock"
    best = resolve_lock(
        f_hz,
        a4_src,
        preferred_pc=preferred_pc,
        midi_lo=midi_lo,
        midi_hi=midi_hi,
        max_abs_cents=max_abs_cents,
    )
    world = tone.world if tone is not None else None
    role = "degree-lock"
    return _result(
        mode=mode,
        a4_src=a4_src,
        a4_target=best["a4"],
        lock=f"{best['note']}={f_hz:.3f}",
        role=role,
        world=world,
        lock_midi=best["midi"],
        f_hz=f_hz,
        preset_id=preset_id,
        ok=best["score"] <= max_abs_cents,
    )
