"""Automated unit tests for musescore_helper.py (PDF inspection, Violin/Piano verification, and Slow Practice Pack)."""
from __future__ import annotations

from fractions import Fraction
import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / ".agents" / "skills" / "pdf-to-musescore" / "scripts" / "musescore_helper.py"

spec = importlib.util.spec_from_file_location("musescore_helper", HELPER_PATH)
mh = importlib.util.module_from_spec(spec)
import sys
sys.modules["musescore_helper"] = mh
spec.loader.exec_module(mh)


def _sample_violin_xml(
    tempo: int = 88,
    sound_tempo: int | None = None,
    bar2_dur: int = 16,
    first_octave: int = 4,
    dangling_tie: bool = False,
) -> str:
    st = sound_tempo if sound_tempo is not None else tempo
    tie_tag = '<tie type="start"/><notations><tied type="start"/></notations>' if dangling_tie else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>Cantabile Violin Study</work-title></work>
  <part-list>
    <score-part id="P1"><part-name>Violin</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
        <key><fifths>2</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <direction placement="above">
        <direction-type>
          <metronome><beat-unit>quarter</beat-unit><per-minute>{tempo}</per-minute></metronome>
        </direction-type>
        <sound tempo="{st}"/>
      </direction>
      <note><pitch><step>D</step><octave>{first_octave}</octave></pitch><duration>8</duration><voice>1</voice><type>half</type></note>
      <note><pitch><step>F</step><alter>1</alter><octave>4</octave></pitch><duration>8</duration><voice>1</voice><type>half</type></note>
    </measure>
    <measure number="2">
      <note><pitch><step>A</step><octave>4</octave></pitch><duration>{bar2_dur}</duration><voice>1</voice><type>whole</type>{tie_tag}</note>
    </measure>
    <measure number="3">
      <note><pitch><step>D</step><octave>5</octave></pitch><duration>16</duration><voice>1</voice><type>whole</type></note>
    </measure>
  </part>
</score-partwise>
"""


def _sample_piano_xml(lh_bars: int = 2) -> str:
    lh_bar2 = (
        """
    <measure number="2">
      <note><pitch><step>G</step><octave>2</octave></pitch><duration>16</duration><voice>1</voice><type>whole</type></note>
    </measure>"""
        if lh_bars >= 2 else ""
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>Minuet in G</work-title></work>
  <part-list>
    <score-part id="P1"><part-name>Piano Right Hand</part-name></score-part>
    <score-part id="P2"><part-name>Piano Left Hand</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
        <key><fifths>1</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <direction placement="above">
        <direction-type>
          <metronome><beat-unit>quarter</beat-unit><per-minute>100</per-minute></metronome>
        </direction-type>
        <sound tempo="100"/>
      </direction>
      <note><pitch><step>D</step><octave>5</octave></pitch><duration>8</duration><voice>1</voice><type>half</type></note>
      <note><pitch><step>B</step><octave>4</octave></pitch><duration>8</duration><voice>1</voice><type>half</type></note>
    </measure>
    <measure number="2">
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>16</duration><voice>1</voice><type>whole</type></note>
    </measure>
  </part>
  <part id="P2">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
        <key><fifths>1</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>F</sign><line>4</line></clef>
      </attributes>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>16</duration><voice>1</voice><type>whole</type></note>
    </measure>{lh_bar2}
  </part>
</score-partwise>
"""


def test_inspect_vector_pdf_and_image():
    ps19 = ROOT / "data" / "input" / "psalms" / "04_Ps-1819-Your-Words-O-Lord.pdf"
    if ps19.exists():
        info = mh.inspect_file(ps19)
        assert info["kind"] == "vector_pdf"
        assert len(info["music_fonts"]) >= 1
    photo = ROOT / "data" / "input" / "Cantabile" / "cantabile.jpeg"
    if photo.exists():
        p_info = mh.inspect_file(photo)
        assert p_info["kind"] == "image_score"


def test_verify_clean_violin_score_passes(tmp_path):
    xml_file = tmp_path / "clean_violin.musicxml"
    xml_file.write_text(_sample_violin_xml(), encoding="utf-8")
    rep = mh.verify_musicxml(xml_file, instrument="violin")
    assert rep["passed"] is True
    assert rep["status"] == "PASS"
    assert rep["instrument"] == "violin"
    assert rep["suspect_bars"] == []
    assert rep["pitch_warnings"] == []


def test_verify_catches_suspect_interior_bar_and_dangling_tie(tmp_path):
    xml_file = tmp_path / "bad_bar.musicxml"
    xml_file.write_text(_sample_violin_xml(bar2_dur=14, dangling_tie=True), encoding="utf-8")
    rep = mh.verify_musicxml(xml_file, instrument="violin")
    assert rep["passed"] is False
    assert len(rep["suspect_bars"]) == 1
    assert rep["suspect_bars"][0]["bar"] == "2"
    assert rep["suspect_bars"][0]["status"] == "SUSPECT_SHORT"
    assert rep["suspect_bars"][0]["diff_beats"] == pytest.approx(-0.5)
    assert len(rep["tie_errors"]) == 1


def test_verify_catches_note_below_violin_open_g3(tmp_path):
    xml_file = tmp_path / "low_violin.musicxml"
    xml_file.write_text(_sample_violin_xml(first_octave=3), encoding="utf-8")  # D3 = MIDI 50 < 55 (G3)
    rep = mh.verify_musicxml(xml_file, instrument="violin")
    assert any(map(lambda w: "below the violin's lowest string" in w, rep["pitch_warnings"]))


def test_verify_catches_piano_hand_bar_count_mismatch(tmp_path):
    xml_file = tmp_path / "desync_piano.musicxml"
    xml_file.write_text(_sample_piano_xml(lh_bars=1), encoding="utf-8")
    rep = mh.verify_musicxml(xml_file, instrument="piano")
    assert rep["passed"] is False
    assert len(rep["sync_errors"]) == 1


def test_verify_catches_metronome_vs_sound_tempo_mismatch(tmp_path):
    xml_file = tmp_path / "bad_tempo.musicxml"
    xml_file.write_text(_sample_violin_xml(tempo=100, sound_tempo=50), encoding="utf-8")
    rep = mh.verify_musicxml(xml_file, instrument="violin")
    assert rep["passed"] is False
    assert len(rep["tempo_warnings"]) == 1


def test_slow_practice_pack_scales_tempos_adds_guide_click_and_preserves_notes(tmp_path):
    xml_file = tmp_path / "violin_piece.musicxml"
    xml_file.write_text(_sample_violin_xml(tempo=88), encoding="utf-8")
    out_dir = tmp_path / "slow_pack"

    pack = mh.generate_slow_practice_pack(
        xml_file,
        out_dir,
        speeds=(1.0, 0.5, 0.33, 0.25, 0.20),
        instrument="violin",
    )
    assert pack["all_parity_verified"] is True
    assert len(pack["practice_files"]) == 5

    by_pct = dict(map(lambda pf: (pf["speed_percent"], pf), pack["practice_files"]))
    assert by_pct[100]["new_bpm"] == 88 and by_pct[100]["guide_click"] is False
    assert by_pct[50]["new_bpm"] == 44 and by_pct[50]["guide_click"] is False
    assert by_pct[33]["new_bpm"] == 29 and by_pct[33]["guide_click"] is True
    assert by_pct[25]["new_bpm"] == 22 and by_pct[25]["guide_click"] is True
    assert by_pct[20]["new_bpm"] == 18 and by_pct[20]["guide_click"] is True

    # Double-check that the 25% ultra-slow MusicXML passes `verify` and includes the subdivision click part
    q_path = Path(by_pct[25]["musicxml"])
    q_rep = mh.verify_musicxml(q_path, reference_path=xml_file, instrument="violin")
    assert q_rep["passed"] is True
    assert q_rep["tempo_bpm"] == pytest.approx(22.0)
    assert q_rep["reference_comparison"]["rhythm_and_pitch_accuracy"] == 1.0
    assert len(ET.parse(q_path).getroot().findall("part")) == 2


def test_piano_hands_separate_slow_pack(tmp_path):
    xml_file = tmp_path / "piano_piece.musicxml"
    xml_file.write_text(_sample_piano_xml(lh_bars=2), encoding="utf-8")
    out_dir = tmp_path / "piano_pack"

    pack = mh.generate_slow_practice_pack(
        xml_file,
        out_dir,
        speeds=(0.5, 0.25),
        instrument="piano",
        hands_separate=True,
    )
    assert pack["all_parity_verified"] is True
    half_info = pack["practice_files"][0]
    rh_path = Path(half_info["hands_separate"]["right_hand_musicxml"])
    lh_path = Path(half_info["hands_separate"]["left_hand_musicxml"])
    assert rh_path.exists() and lh_path.exists()
    assert mh.extract_sounding_sequence(rh_path) == [(74, Fraction(2)), (71, Fraction(2)), (67, Fraction(4))]
    assert mh.extract_sounding_sequence(lh_path) == [(55, Fraction(4)), (43, Fraction(4))]

# <!-- APAF Bioinformatics | test_musescore_helper.py | Approved | 2026-11-02 -->

