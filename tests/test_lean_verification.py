"""Lean 4 verification tests & Gate D5 disk falsifiers (loop-free)."""

from __future__ import annotations

import os
import re
import sys
from fractions import Fraction
from pathlib import Path

import mido
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import lean_bridge
import music_pipeline
import psalms_db
import score_formatter


def _write_psalm_artifacts(psalm_data: dict, out_dir: Path, speed: float = 1.0, augment: int = 1) -> tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    xml_p = out_dir / "score.musicxml"
    ly_p = out_dir / "score.ly"
    mid_p = out_dir / "score.mid"
    xml_p.write_text(score_formatter.export_musicxml(psalm_data, speed=speed, augment=augment), encoding="utf-8")
    ly_p.write_text(score_formatter.export_lilypond(psalm_data, speed=speed, augment=augment), encoding="utf-8")
    mid_p.write_bytes(score_formatter.export_midi(psalm_data, speed=speed, augment=augment))
    return xml_p, ly_p, mid_p


def test_psalm_roundtrip_and_slowdown_lean_verified(tmp_path: Path):
    """Validates MusicXML, LilyPond, and MIDI across full, half, and augmented editions."""
    psalm = psalms_db.get_psalm("psalm_103_kind_chart")
    assert psalm is not None
    ref_spec = lean_bridge.spec_from_psalm_data(psalm, speed=1.0, augment=1, pad_incomplete_bars=True)

    xml_full, ly_full, mid_full = _write_psalm_artifacts(psalm, tmp_path / "full", speed=1.0, augment=1)
    xml_half, ly_half, mid_half = _write_psalm_artifacts(psalm, tmp_path / "half", speed=0.5, augment=1)
    xml_aug, ly_aug, mid_aug = _write_psalm_artifacts(psalm, tmp_path / "aug", speed=0.5, augment=2)

    mid_f_notes, mid_f_tn, mid_f_td = lean_bridge.sounding_notes_from_midi_file(mid_full)
    mid_h_notes, mid_h_tn, mid_h_td = lean_bridge.sounding_notes_from_midi_file(mid_half)
    mid_a_notes, mid_a_tn, mid_a_td = lean_bridge.sounding_notes_from_midi_file(mid_aug)

    report = lean_bridge.verify_bundle_with_lean(
        reference=("original", ref_spec),
        score_entries=(
            ("xml_full", lean_bridge.spec_from_musicxml_file(xml_full), 1, 1, 1),
            ("ly_full", lean_bridge.spec_from_lilypond_file(ly_full), 1, 1, 1),
            ("xml_half", lean_bridge.spec_from_musicxml_file(xml_half), 1, 1, 2),
            ("ly_half", lean_bridge.spec_from_lilypond_file(ly_half), 1, 1, 2),
            ("xml_aug", lean_bridge.spec_from_musicxml_file(xml_aug), 2, 1, 2),
            ("ly_aug", lean_bridge.spec_from_lilypond_file(ly_aug), 2, 1, 2),
        ),
        note_entries=(
            ("mid_full", mid_f_notes, 1, 1, 1, mid_f_tn, mid_f_td),
            ("mid_half", mid_h_notes, 1, 1, 2, mid_h_tn, mid_h_td),
            ("mid_aug", mid_a_notes, 2, 1, 2, mid_a_tn, mid_a_td),
        ),
    )
    assert report["ok"] is True, f"Unexpected Lean verification failure: {report}"
    assert report["all_bars_valid"] is True
    assert report["failures"] == []


def test_real_vector_pdf_full_kernel_certificate(tmp_path: Path):
    """Converts a real vector PDF in data/ and proves equivalence in the Lean 4 kernel (`lake env lean`)."""
    pdf_path = ROOT / "data" / "03_Ps104103-Lord-Send-Out-Your-Spirit-Chart.pdf"
    assert pdf_path.is_file()

    rep = music_pipeline.run_convert_pipeline(
        pdf_path,
        tmp_path,
        speeds=(Fraction(1, 1), Fraction(1, 2)),
        lean_cert=True,
    )
    lv = rep["lean_verification"]
    assert lv["ok"] is True, f"Lean verification failed: {lv}"
    assert lv["lean_cert_ok"] is True, lv.get("lean_cert_output", "")
    assert Path(lv["lean_cert_path"]).is_file()


def _synthetic_tied_score() -> dict:
    return {
        "id": "synthetic_tie_test",
        "title": "Synthetic Tie Test",
        "composer": "Test",
        "key": "C Major",
        "key_signature": "0",
        "time_signature": "4/4",
        "tempo": 80,
        "response": {
            "notes": [
                {"pitch": "C4", "midi": 60, "duration": "half", "beats": 2.0, "lyric": "One"},
                {"pitch": "D4", "midi": 62, "duration": "half", "beats": 2.0, "tie": "start", "lyric": "Two"},
                {"pitch": "D4", "midi": 62, "duration": "half", "beats": 2.0, "tie": "stop", "lyric": ""},
                {"pitch": "E4", "midi": 64, "duration": "half", "beats": 2.0, "lyric": "Three"},
            ],
            "accompaniment": [],
        },
    }


def test_d5_falsifier_corrupt_xml_interior_bar_duration(tmp_path: Path):
    """Falsifier A: dropping 24 ticks from bar 1 on disk MUST be caught."""
    psalm = _synthetic_tied_score()
    ref_spec = lean_bridge.spec_from_psalm_data(psalm, pad_incomplete_bars=True)
    xml_p, _, _ = _write_psalm_artifacts(psalm, tmp_path)

    xml_text = xml_p.read_text(encoding="utf-8")
    corrupt = re.sub(r"<duration>96</duration>", "<duration>72</duration>", xml_text, count=1)
    assert corrupt != xml_text
    xml_p.write_text(corrupt, encoding="utf-8")

    rep = lean_bridge.verify_bundle_with_lean(
        reference=("original", ref_spec),
        score_entries=(("xml_corrupt", lean_bridge.spec_from_musicxml_file(xml_p), 1, 1, 1),),
    )
    assert rep["ok"] is False
    assert rep["all_bars_valid"] is False
    assert any(map(lambda f: "bar 1" in f.lower() and "ticks" in f.lower(), rep["failures"]))


def test_d5_falsifier_inflate_lilypond_bar_duration(tmp_path: Path):
    """Falsifier B: inflating bar 1 in `.ly` on disk MUST be caught."""
    psalm = _synthetic_tied_score()
    ref_spec = lean_bridge.spec_from_psalm_data(psalm, pad_incomplete_bars=True)
    _, ly_p, _ = _write_psalm_artifacts(psalm, tmp_path)

    ly_text = ly_p.read_text(encoding="utf-8")
    corrupt = ly_text.replace("c'2 d'2~ |", "c'2 d'2.~ |", 1)
    assert corrupt != ly_text
    ly_p.write_text(corrupt, encoding="utf-8")

    rep = lean_bridge.verify_bundle_with_lean(
        reference=("original", ref_spec),
        score_entries=(("ly_corrupt", lean_bridge.spec_from_lilypond_file(ly_p), 1, 1, 1),),
    )
    assert rep["ok"] is False
    assert rep["all_bars_valid"] is False
    assert any(map(lambda f: "bar 1" in f.lower(), rep["failures"]))


def test_d5_falsifier_shift_lilypond_pitch_preserving_beats(tmp_path: Path):
    """Falsifier C: changing one pitch in `.ly` while preserving bar beats MUST fail sounding equivalence."""
    psalm = _synthetic_tied_score()
    ref_spec = lean_bridge.spec_from_psalm_data(psalm, pad_incomplete_bars=True)
    _, ly_p, _ = _write_psalm_artifacts(psalm, tmp_path)

    ly_text = ly_p.read_text(encoding="utf-8")
    corrupt = ly_text.replace("e'2 |", "f'2 |", 1)
    assert corrupt != ly_text
    ly_p.write_text(corrupt, encoding="utf-8")

    rep = lean_bridge.verify_bundle_with_lean(
        reference=("original", ref_spec),
        score_entries=(("ly_pitch_swap", lean_bridge.spec_from_lilypond_file(ly_p), 1, 1, 1),),
    )
    assert rep["ok"] is False
    assert rep["all_bars_valid"] is True
    assert any(map(lambda f: "mismatch" in f.lower(), rep["failures"]))


def test_d5_falsifier_drop_xml_tie(tmp_path: Path):
    """Falsifier D: removing `<tie type=\"start\"/>` so one tied note becomes two attacks MUST fail."""
    psalm = _synthetic_tied_score()
    ref_spec = lean_bridge.spec_from_psalm_data(psalm, pad_incomplete_bars=True)
    xml_p, _, _ = _write_psalm_artifacts(psalm, tmp_path)

    xml_text = xml_p.read_text(encoding="utf-8")
    corrupt = xml_text.replace('<tie type="start"/>', "").replace('<tie type="stop"/>', "")
    assert corrupt != xml_text
    xml_p.write_text(corrupt, encoding="utf-8")

    rep = lean_bridge.verify_bundle_with_lean(
        reference=("original", ref_spec),
        score_entries=(("xml_broken_tie", lean_bridge.spec_from_musicxml_file(xml_p), 1, 1, 1),),
    )
    assert rep["ok"] is False
    assert rep["all_bars_valid"] is True
    assert any(map(lambda r: r["name"] == "xml_broken_tie" and not r["equiv_to_ref"], rep["representations"]))


def test_d5_falsifier_corrupt_midi_pitch_on_disk(tmp_path: Path):
    """Falsifier E: altering a single MIDI note number on disk MUST fail."""
    psalm = _synthetic_tied_score()
    ref_spec = lean_bridge.spec_from_psalm_data(psalm, pad_incomplete_bars=True)
    _, _, mid_p = _write_psalm_artifacts(psalm, tmp_path)

    mid = mido.MidiFile(str(mid_p))
    first_on = next(filter(lambda m: m.type == "note_on" and m.velocity > 0, mid.tracks[0]))
    orig_pitch = first_on.note
    first_on.note = orig_pitch + 2
    first_off = next(filter(lambda m: (m.type == "note_off" or (m.type == "note_on" and m.velocity == 0)) and m.note == orig_pitch, mid.tracks[0]))
    first_off.note = orig_pitch + 2
    mid.save(str(mid_p))

    m_notes, m_tn, m_td = lean_bridge.sounding_notes_from_midi_file(mid_p)
    rep = lean_bridge.verify_bundle_with_lean(
        reference=("original", ref_spec),
        note_entries=(("mid_corrupt", m_notes, 1, 1, 1, m_tn, m_td),),
    )
    assert rep["ok"] is False
    assert any(map(lambda r: r["name"] == "mid_corrupt" and not r["equiv_to_ref"], rep["representations"]))


def test_psalm_122_as_written_and_full_arrangement_lean_kernel(tmp_path: Path):
    """Real vector PDF with Sibelius cue pickup passes Lean kernel in both chart and arrangement modes."""
    pdf_path = ROOT / "data" / "Ps-122-I-Rejoiced-Chart.pdf"
    rep1 = music_pipeline.run_convert_pipeline(
        pdf_path,
        tmp_path / "as_written",
        speeds=(Fraction(1, 1), Fraction(1, 2)),
        lean_cert=True,
        arrangement=False,
    )
    assert rep1["lean_verification"]["ok"] is True
    assert rep1["lean_verification"]["lean_cert_ok"] is True
    assert rep1["lean_verification"]["checked_bars"] == 28

    rep2 = music_pipeline.run_convert_pipeline(
        pdf_path,
        tmp_path / "arr",
        speeds=(Fraction(1, 1), Fraction(1, 2)),
        lean_cert=True,
        arrangement=True,
    )
    assert rep2["lean_verification"]["ok"] is True
    assert rep2["lean_verification"]["lean_cert_ok"] is True
    assert rep2["lean_verification"]["checked_bars"] == 40


# <!-- APAF Bioinformatics | test_lean_verification.py | Approved | 2026-11-15 -->
