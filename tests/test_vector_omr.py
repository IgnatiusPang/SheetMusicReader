"""Tests for vector_omr: glyph tables, pitch spelling, rhythm repair, tuplets, durations and an end-to-end PDF check."""
import shutil
from pathlib import Path

import mido
import pytest

import vector_omr as v

ROOT = Path(__file__).resolve().parents[1]
PS19 = ROOT / "data" / "04_Ps-1819-Your-Words-O-Lord.pdf"


@pytest.mark.parametrize("font, text, role", [
    ("ABCDEF+Leland", "", ("head", 1.0)),
    ("ABCDEF+Bravura", "", ("acc", 1)),
    ("Opus", "œ", ("head", 1.0)),        # MacRoman-mapped Sibelius notehead (byte 0xCF)
    ("Opus", "", ("head", 1.0)),        # same glyph, symbol-PUA encoding
    ("OpusSpecial", "™", ("dot", None)),
    ("TTE1BC7958t00", "", ("head", 2.0)),
    ("MScoreRegular", "", ("head", 2.0)),
])
def test_glyph_roles_across_notation_fonts(font, text, role):
    assert v.glyph_role(font, text) == role


@pytest.mark.parametrize("font", ["OpusText", "LelandText", "OpusChords", "TimesNewRomanPSMT"])
def test_text_fonts_are_not_music_glyphs(font):
    assert v.glyph_role(font, "q") is None


@pytest.mark.parametrize("d, alter, midi", [(30, 0, 64), (28, 0, 60), (31, 1, 66), (34, -1, 70), (18, 0, 43)])
def test_diatonic_to_midi(d, alter, midi):
    assert v.diatonic_to_midi(d, alter) == midi


def test_key_alterations_follow_circle_of_fifths():
    assert v.key_alter(2, 3) == 1 and v.key_alter(2, 0) == 1 and v.key_alter(2, 4) == 0   # D major: F#, C#
    assert v.key_alter(-3, 6) == -1 and v.key_alter(-3, 5) == -1 and v.key_alter(-3, 1) == 0  # Eb major


def _note(x, value, stem=1, midi=60):
    head = v.Head(x, 0, 6, value, 28, midi, stem, 0, 0, value)
    return v.Event(x, value, (head,), stem)


def test_triplets_scale_three_equal_notes_in_an_overfull_bar():
    bar = (_note(0, 1), _note(10, 1), _note(20, 1), _note(30, 1), _note(40, 1))
    fixed = v.repair(bar, 4.0)
    assert sum(map(lambda e: e.value, fixed)) == pytest.approx(4.0)


def test_repair_keeps_upper_voice_when_two_voices_share_a_staff():
    bar = (_note(0, 1.5, 1), _note(0, 1.5, -1, 55), _note(10, 1.5, 1), _note(10, 1.5, -1, 55))
    fixed = v.repair(bar, 3.0)
    assert list(map(lambda e: e.stem, fixed)) == [1, 1]


def test_whole_rest_fills_the_bar():
    assert v.repair((v.Event(0, 4.0),), 3.0)[0].value == 3.0


def test_duplet_number_lengthens_two_eighths_in_compound_time():
    events = [_note(100, 0.5), _note(110, 0.5), _note(130, 1.0)]
    two = v.Glyph("tuplet", 2, 108, -10, 4, 9)
    scaled = v.apply_tuplets(events, [two], sp=4.5)
    assert list(map(lambda e: e.value, scaled)) == [0.75, 0.75, 1.0]


@pytest.mark.parametrize("value, lily", [(1.5, "4."), (0.25, "16"), (3.0, "2."), (2 / 3, "4*2/3")])
def test_lily_durations(value, lily):
    assert v.lily_duration(value) == lily


@pytest.mark.skipif(not PS19.exists() or shutil.which("pdftoppm") is None, reason="needs the Psalm 19 PDF and poppler")
def test_end_to_end_psalm_19(tmp_path):
    score = v.read_score(PS19)
    assert score.report["key"] == 2 and score.report["time"] == [6, 8]
    assert score.tempo == pytest.approx(72.0)                      # dotted quarter = 48
    assert score.report["measures"] == 36 and score.report["full"] == 36 and not score.report["suspect"]
    midi = mido.MidiFile(v.write_midi(score, tmp_path / "ps19.mid", as_written=True))
    notes = list(filter(lambda m: m.type == "note_on" and m.velocity > 0, midi.tracks[0]))
    assert notes[0].note == 66                                      # first note F#4 after the eighth rest
    assert len(notes) < score.report["notes"]                       # tied notes merged into single MIDI notes
    assert score.report["playback"] == "R V1 R V2 R V3 R V4 R*"


PS80 = ROOT / "data" / "03_Ps-8079-Lord-Make-Us-Turn-To-You.pdf"
PS106 = ROOT / "data" / "04_psalm-106-oz-12th-sunday-year-b-compact.pdf"
needs = lambda f: pytest.mark.skipif(not f.exists() or shutil.which("pdftoppm") is None, reason="needs the PDF and poppler")


def _timeline(path):
    from functools import reduce
    def step(acc, msg):
        t, out = acc
        t += msg.time
        return t, out + ([(t / 480, msg.note)] if msg.type == "note_on" and msg.velocity else [])
    return reduce(step, mido.MidiFile(path).tracks[0], (0, []))[1]


@needs(PS80)
def test_psalm_80_sections_and_verse_pickup(tmp_path):
    score = v.read_score(PS80)
    assert score.report["sections"] == "R[s1] V1[s2,s3] V2[s4,s5] V3[s6,s7]"
    assert (score.report["pickup_notes"], score.report["pickup_kind"]) == (2, "extra")
    notes = _timeline(v.write_midi(score, tmp_path / "ps80.mid"))
    before_v1 = list(map(lambda n: n[1], filter(lambda n: 16 <= n[0] < 17, notes)))
    assert before_v1 == [62, 65]                                    # D4 F4 pickup leads into verse 1 (bar 5 starts at beat 17)
    assert notes[-1][1] == 65 and notes[-2][1] != 62                # final response ends on F4 without the pickup


@needs(PS106)
def test_psalm_106_stacked_verse_staves_map_to_their_own_verse():
    secs = v.sections_of(v.read_score(PS106))
    verses = dict(map(lambda s: (s.num, s.parts[0][1]), filter(lambda s: s.kind == "verse", secs)))
    assert verses == {1: 0, 2: 1, 3: 2, 4: 3}


def test_arrangement_alternates_response_and_verses(monkeypatch):
    resp, v1, v2 = (v.Section("response", 0, ((0, 0, ()),)), v.Section("verse", 1, ((1, 0, ()),)),
                    v.Section("verse", 2, ((2, 0, ()),)))
    monkeypatch.setattr(v, "sections_of", lambda score: [resp, v1, v2])
    order = list(map(lambda sf: (sf[0].kind, sf[0].num, sf[1]), v.arrangement(None)))
    assert order == [("response", 0, False), ("verse", 1, False), ("response", 0, False), ("verse", 2, False), ("response", 0, True)]

# <!-- APAF Bioinformatics | test_vector_omr.py | Approved | 2026-10-25 -->
