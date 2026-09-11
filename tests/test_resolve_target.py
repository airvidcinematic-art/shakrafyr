"""Palette worlds + resolve_target façade.

Regression core: sub-audio rates must RAISE instead of emitting an absurd A4.
DSP primitive stays ratio = A4_target / A4_src.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.palette import (  # noqa: E402
    AUDIO_FLOOR_HZ,
    HEART_A4,
    MODULATION_PRESETS,
    PALETTE,
    RIFE_BLOCKLIST_HZ,
    WORLDS,
    get_tone,
)
from tools.resolve_target import (  # noqa: E402
    SubAudioTargetError,
    a4_for_lock,
    resolve_modulation,
    resolve_target,
)

A440 = 440.0


def test_heart_lock_golden_a4():
    assert a4_for_lock(528.0, 72) == pytest.approx(443.9933072539613)
    assert HEART_A4 == pytest.approx(443.9933072539613)


def test_heart_528_is_world_444():
    r = resolve_target(a4_src=A440, mode="solfeggio_lock", preset_id="heart_528")
    assert r["world"] == "world_444"
    assert r["role"] == "degree-lock"
    assert r["a4_target"] == pytest.approx(HEART_A4)
    assert r["ratio"] == pytest.approx(r["a4_target"] / A440)
    assert r["lock_midi"] == 72


def test_world_444_concert_matches_heart_a4():
    r = resolve_target(a4_src=A440, mode="concert_a", preset_id="world_444")
    assert r["world"] == "world_444"
    assert r["a4_target"] == pytest.approx(HEART_A4, abs=1e-6)
    assert r["ratio"] == pytest.approx(r["a4_target"] / A440)


def test_concert_432_stays_its_own_world():
    r = resolve_target(a4_src=A440, mode="concert_a", preset_id="concert_432")
    assert r["world"] == "world_432"
    assert r["a4_target"] == pytest.approx(432.0)
    assert r["ratio"] == pytest.approx(432.0 / 440.0)


@pytest.mark.parametrize(
    "f_hz, midi, a4, tol",
    [
        (111.0, 45, 444.0, 1e-9),       # A2
        (888.0, 81, 444.0, 1e-9),       # A5
        (136.10, 49, 432.09, 0.05),     # C#3 OM
        (172.06, 53, 433.56, 0.05),     # F3 platonic year
        (194.18, 55, 435.92, 0.05),     # G3 earth day
        (2172.0, 96, 456.61, 0.05),     # C7 extended, edge
    ],
)
def test_handoff_lock_vectors(f_hz: float, midi: int, a4: float, tol: float):
    r = resolve_target(a4_src=A440, mode="solfeggio_lock", f_hz=f_hz)
    assert r["lock_midi"] == midi
    assert r["a4_target"] == pytest.approx(a4, abs=tol)
    assert r["ratio"] == pytest.approx(r["a4_target"] / A440)


def test_2172_is_edge_not_rejected():
    r = resolve_target(a4_src=A440, mode="solfeggio_lock", f_hz=2172.0)
    assert r["band"] == "edge"
    assert r["ok"] is True
    shift = abs(r["shift_cents"])
    assert 50.0 < shift <= 80.0


def test_7_83_raises_instead_of_absurd_a4():
    with pytest.raises(SubAudioTargetError):
        resolve_target(a4_src=A440, mode="solfeggio_lock", f_hz=7.83)
    with pytest.raises(SubAudioTargetError):
        resolve_target(a4_src=A440, mode="solfeggio_lock", preset_id="schumann_7_83")


def test_40_raises_instead_of_absurd_a4():
    with pytest.raises(SubAudioTargetError):
        resolve_target(a4_src=A440, mode="solfeggio_lock", f_hz=40.0)
    with pytest.raises(SubAudioTargetError):
        resolve_target(a4_src=A440, mode="solfeggio_lock", preset_id="gamma_40")


def test_audio_floor_is_sixty():
    assert AUDIO_FLOOR_HZ == 60.0
    with pytest.raises(SubAudioTargetError):
        resolve_target(a4_src=A440, mode="solfeggio_lock", f_hz=59.99)
    r = resolve_target(a4_src=A440, mode="solfeggio_lock", f_hz=60.0)
    assert r["a4_target"] > 0
    assert r["ratio"] == pytest.approx(r["a4_target"] / A440)


def test_modulation_mode_is_not_a_pitch_ratio():
    with pytest.raises((SubAudioTargetError, ValueError)):
        resolve_target(a4_src=A440, mode="modulation_rate", f_hz=7.83)


def test_modulation_plan_schumann_sidebands():
    plan = resolve_modulation(7.83, carrier_hz=528.0)
    assert plan["mode"] == "modulation_rate"
    assert plan["rate_hz"] == pytest.approx(7.83)
    assert plan["binaural"]["left_hz"] == pytest.approx(200.0)
    assert plan["binaural"]["right_hz"] == pytest.approx(207.83)
    assert plan["binaural"]["headphone_only"] is True
    assert plan["binaural"]["ship"] is True
    assert plan["tone_gate"]["ship"] is True
    assert plan["tone_gate"]["on"] == "standalone_tone"
    # Physics of AM sidebands is recorded, but music-AM must not ship.
    assert plan["music_am"]["ship"] is False
    assert plan["music_am"]["flag"] == "music_am_disabled"
    assert plan["music_am"]["sidebands"]["lower"] == pytest.approx(520.17, abs=0.01)
    assert plan["music_am"]["sidebands"]["upper"] == pytest.approx(535.83, abs=0.01)
    assert "a4_target" not in plan


def test_modulation_plan_gamma_40():
    plan = resolve_modulation(40.0, carrier_hz=528.0)
    assert plan["music_am"]["ship"] is False
    assert plan["music_am"]["sidebands"]["lower"] == pytest.approx(488.0)
    assert plan["music_am"]["sidebands"]["upper"] == pytest.approx(568.0)
    assert plan["binaural"]["ship"] is True


def test_solar_day_is_194_18_not_sidereal():
    solar = get_tone("root_194")
    assert solar is not None
    assert solar.freq_hz == pytest.approx(194.18)
    assert "sidereal" not in solar.label.lower()
    assert "sidereal" not in solar.desc.split(".")[0].lower()
    sidereal = get_tone("sidereal_194")
    assert sidereal is not None
    assert sidereal.freq_hz == pytest.approx(194.71)


def test_111_preset_is_not_labelled_hypogeum_resonance():
    tone = get_tone("hypogeum_111")
    assert tone is not None
    blob = f"{tone.label} {tone.id} {tone.desc}".lower()
    assert "hypogeum resonance" not in blob
    assert tone.freq_hz == pytest.approx(111.0)


def test_gamma_40_has_all_three_roles():
    tone = get_tone("gamma_40")
    assert tone is not None
    assert set(tone.roles) == {"degree-lock", "modulation-rate", "physical-vibration"}
    assert tone.family == "geophysical"


def test_palette_families_and_worlds():
    all_tones = list(PALETTE) + list(MODULATION_PRESETS)
    families = {t.family for t in all_tones}
    for needed in (
        "solfeggio",
        "cosmic_octave",
        "numeric_lock",
        "archaeoacoustics",
        "instrument",
        "extended_set",
        "geophysical",
    ):
        assert needed in families
    assert "world_444" in WORLDS
    assert "world_432" in WORLDS
    assert WORLDS["world_444"].a4 == pytest.approx(HEART_A4, abs=1e-6)
    cosmic = [t for t in PALETTE if t.family == "cosmic_octave"]
    assert len(cosmic) >= 9
    for tid in (
        "om_136",
        "hypogeum_111",
        "newgrange_110",
        "fork_128",
        "c256",
        "num_111",
        "num_888",
        "ext_1074",
        "ext_1152",
        "ext_1174",
        "ext_2172",
    ):
        assert get_tone(tid) is not None


def test_no_rife_disease_frequencies():
    all_tones = list(PALETTE) + list(MODULATION_PRESETS)
    hz = {round(t.freq_hz) for t in all_tones}
    assert RIFE_BLOCKLIST_HZ.isdisjoint(hz)
    ids = {t.id for t in all_tones}
    assert not any("rife" in i for i in ids)


def test_bypass_ratio_is_one():
    r = resolve_target(a4_src=443.0, mode="bypass")
    assert r["ratio"] == pytest.approx(1.0)
    assert r["a4_target"] == pytest.approx(443.0)
