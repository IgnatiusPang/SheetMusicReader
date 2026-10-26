"""Tests for score_from_image: notation helpers, bar validation, mark merging, Claude refinement (fake client),
LilyPond output and an end-to-end photo conversion. Run with the omr env:
    /Users/ignatiuspang/anaconda3/envs/omr/bin/python -m pytest tests/test_score_from_image.py
"""
import importlib.util
import json
import shutil
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import score_from_image as s

ROOT = Path(__file__).resolve().parents[1]
PHOTO = ROOT / "data" / "Cantabile" / "cantabile.jpeg"
TRUTH = ROOT / "digitized_scores" / "cantabile.midi"
F = Fraction


def ev(p, d, **kw):
    return s.Ev(tuple(p.split()) if p else (), F(d), **kw)


def score_of(*bars, time=(4, 4), breaks=(0,)):
    return s.Score(parts=(s.Part("treble", tuple(map(lambda b: s.Bar(tuple(b)), bars))),), breaks=breaks, time=time)


@pytest.mark.parametrize("step, alter, octave, name, midi", [
    ("C", 0, 4, "c'", 60), ("F", 1, 5, "fis''", 78), ("B", -1, 3, "bes", 58), ("G", 0, 2, "g,", 43),
    ("E", -1, 4, "ees'", 63), ("D", 2, 4, "disis'", 64)])
def test_pitch_names_and_midi(step, alter, octave, name, midi):
    assert s.lily_pitch(step, alter, octave) == name
    assert s.pitch_midi(name) == midi


@pytest.mark.parametrize("q, text", [(F(4), "1"), (F(3, 2), "4."), (F(7, 4), "4.."), (F(1, 4), "16"),
                                     (F(2, 3), "4*2/3"), (F(1, 3), "8*2/3"), (F(6), "1.")])
def test_durations_round_trip(q, text):
    assert s.lily_duration(q) == text
    assert s.parse_duration(text) == q


def test_bad_duration_is_rejected():
    with pytest.raises(ValueError):
        s.parse_duration("5")


def test_triplet_runs_become_tuplet_groups():
    text = s.events_text((ev("c'", F(1, 3)), ev("d'", F(1, 3)), ev("e'", F(1, 3)), ev("f'", 1)))
    assert text == "\\tuplet 3/2 { c'8 d'8 e'8 } f'4"


def test_mark_order_breath_and_text():
    e = ev("b'", F(3, 2), marks=("(", ")", "\\downbow", "-1", "text:riten.", "\\breathe"))
    assert s.ev_text(e) == "b'4.)\\downbow-1^\\markup \\italic \"riten.\"( \\breathe"
    assert s.ev_text(ev("c' e' g'", 2, tie=True)) == "<c' e' g'>2~"


def test_bar_check_kinds():
    sc = score_of([ev("c'", 1)], [ev("c'", 4)], [ev("c'", 2)], [ev("c'", 4), ev("d'", 1)], [ev("c'", 2)])
    kinds = list(map(lambda r: (r["bar"], r["kind"]), s.bar_check(sc)))
    assert kinds == [(1, "pickup"), (3, "short"), (4, "over"), (5, "closing")]
    assert list(map(lambda r: r["bar"], s.suspect_bars(s.bar_check(sc)))) == [3, 4]


def test_time_change_sets_expected_length():
    sc = s.Score(parts=(s.Part("treble", (s.Bar((ev("c'", 4),)), s.Bar((ev("c'", 3),), ("\\time 3/4",)))),),
                 breaks=(0,))
    assert s.bar_check(sc) == []


def test_fix_pairs_drops_runaway_hairpins_and_stray_closers():
    sc = score_of([ev("c'", 1, marks=("\\!",)), ev("d'", 1, marks=("\\<",)), ev("e'", 2)])
    clean = s.tidy(sc).parts[0].bars[0].events
    assert list(map(lambda e: e.marks, clean)) == [(), (), ()]


def test_fix_pairs_keeps_closed_slurs_and_drops_nested_start():
    sc = score_of([ev("c'", 1, marks=("(",)), ev("d'", 1, marks=("(",)), ev("e'", 1, marks=(")",)), ev("f'", 1)])
    marks = list(map(lambda e: e.marks, s.tidy(sc).parts[0].bars[0].events))
    assert marks == [("(",), (), (")",), ()]


def test_merge_marks_aligns_by_pitch_and_filters_groups():
    base = score_of([ev("c'", 1), ev("d'", 1), ev("e'", 2)])
    other = score_of([ev("c'", 1, marks=("\\downbow", "-.")), ev("g'", 1), ev("d'", 1, marks=("\\p",)),
                      ev("e'", 1, marks=("\\fermata",))])
    merged, n = s.merge_marks(base, other, 0, {"bowing", "dynamics"})
    assert n == 2
    assert list(map(lambda e: e.marks, merged.parts[0].bars[0].events)) == [("\\downbow",), ("\\p",), ()]


def test_bars_from_json_validates():
    good = {"bars": [{"changes": ["\\key d \\major", "\\bogus"], "events": [
        {"pitches": ["fis''"], "duration": "4.", "tie": False, "grace": False, "marks": ["\\downbow", "zzz", "-3"]}]}]}
    parts, problems = s.bars_from_json([good])
    e = parts[0][0].events[0]
    assert e.marks == ("\\downbow", "-3") and parts[0][0].changes == ("\\key d \\major",)
    assert any(map(lambda p: "zzz" in p, problems)) and any(map(lambda p: "bogus" in p, problems))
    bad = {"bars": [{"changes": [], "events": [{"pitches": ["H4"], "duration": "4", "tie": False, "grace": False,
                                                "marks": []}]}]}
    assert any(map(lambda p: p.startswith("fatal"), s.bars_from_json([bad])[1]))


def _reply(obj):
    return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(obj))],
                           usage=SimpleNamespace(input_tokens=1000, output_tokens=200, cache_read_input_tokens=0))


class FakeClient:
    """Answers system requests from a queue and header requests with a fixed header."""
    def __init__(self, system_replies):
        self.queue, self.calls = list(system_replies), []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls.append(kw)
        if kw["output_config"]["format"]["schema"] is s.HEADER_SCHEMA:
            return _reply({"title": "Cantabile", "subtitle": "", "composer": "Dancla", "arranger": "",
                           "tempo_text": "Andante", "tempo_beat": "4", "tempo_bpm": 80, "time_symbol": "numeric"})
        return _reply(self.queue.pop(0))


def _bar_json(*events):
    return {"changes": [], "events": list(map(lambda e: s.ev_json(e), events))}


def test_refine_retries_bad_bars_then_splices_corrections():
    draft = score_of([ev("c'", 4)], [ev("d'", 2), ev("e'", 1)], [ev("f'", 4)], breaks=(0,))
    short = {"parts": [{"bars": [_bar_json(ev("c'", 4)), _bar_json(ev("d'", 2)), _bar_json(ev("f'", 4))]}],
             "notes": "first try"}
    fixed = {"parts": [{"bars": [_bar_json(ev("c'", 4, marks=("\\p",))),
                                 _bar_json(ev("d'", 2), ev("e'", 2, marks=("\\downbow",))),
                                 _bar_json(ev("f'", 4))]}], "notes": "added e'"}
    client = FakeClient([short, fixed])
    strip = [Image.new("L", (1280, 256), 255)]
    refined, log = s.claude_pass(draft, [strip], Image.new("L", (800, 1000), 255), s.MODEL, workers=1, client=client)
    assert len(list(filter(lambda c: c["output_config"]["format"]["schema"] is s.SYSTEM_SCHEMA, client.calls))) == 2
    assert log["systems"][0]["accepted"] and s.bar_check(refined) == []
    assert refined.parts[0].bars[1].events[1].marks == ("\\downbow",)
    assert (refined.title, refined.composer, refined.tempo) == ("Cantabile", "Dancla", ("4", 80))
    assert log["cost_usd"] > 0
    first = client.calls[0]
    assert first["model"] == s.MODEL and first["fallbacks"] == "default"


def test_refine_keeps_draft_when_answer_stays_invalid():
    draft = score_of([ev("c'", 4)], breaks=(0,))
    broken = {"parts": [{"bars": [{"changes": [], "events": [
        {"pitches": ["x"], "duration": "4", "tie": False, "grace": False, "marks": []}]}]}], "notes": ""}
    client = FakeClient([broken, broken])
    refined, log = s.claude_pass(draft, [[Image.new("L", (640, 256), 255)]], Image.new("L", (100, 100)), s.MODEL,
                                 workers=1, client=client)
    assert not log["systems"][0]["accepted"]
    assert refined.parts[0].bars == draft.parts[0].bars


def test_lilypond_source_breaks_and_irregular_bars():
    sc = score_of([ev("c'", 1)], [ev("d'", 4)], [ev("e'", 3)], [ev("f'", 4)], breaks=(0, 2))
    src = s.lilypond_source(sc)
    layout_score = src.split("\\layout")[0]
    assert "\\partial 4" in layout_score and layout_score.count("\\break") == 1
    assert "\\set Timing.measureLength = #3/4" in src and "\\set Timing.measureLength = #1" in src
    review = s.lilypond_source(sc, (1,), review=True, suspects={(1, 3)})
    assert "\\set Score.currentBarNumber = #3" in review and "with-color #red" in review and "\\break" not in review


@pytest.mark.skipif(shutil.which("lilypond") is None, reason="needs LilyPond")
def test_lilypond_compiles(tmp_path):
    sc = score_of([ev("b'", F(3, 2), marks=("(", "\\downbow", "\\p")), ev("c''", F(1, 2), marks=(")",)),
                   ev("d''", 1, marks=("\\<",)), ev("g''", 1, marks=("\\!", "-3"))],
                  [ev("a'", F(1, 3)), ev("b'", F(1, 3)), ev("c''", F(1, 3)), ev("", 3)])
    ly = tmp_path / "t.ly"
    ly.write_text(s.lilypond_source(replace_key(sc)))
    s.run_lilypond(ly, tmp_path / "t")
    assert (tmp_path / "t.pdf").exists() and (tmp_path / "t.midi").exists()


def replace_key(sc):
    from dataclasses import replace
    return replace(sc, key=(1, "major"), title="Test", tempo=("4", 88), tempo_text="Andante")


@pytest.mark.skipif(not PHOTO.exists() or not TRUTH.exists() or importlib.util.find_spec("homr") is None
                    or shutil.which("lilypond") is None, reason="needs the cantabile photo, homr and LilyPond")
def test_end_to_end_cantabile_photo(tmp_path):
    report = s.convert(PHOTO, tmp_path, use_audiveris=False, title="Cantabile")
    assert report["homr"] == {"systems": 9, "parts": 1, "bars": 41, "staff_images": True}
    assert len(report["bars"]["suspect"]) <= 3
    agreement = s.compare(Path(report["outputs"]["midi"]), TRUTH)
    assert agreement["pitch_accuracy"] >= 0.98 and agreement["full_accuracy"] >= 0.93
    assert Path(report["outputs"]["review"]).stat().st_size > 50_000

# <!-- APAF Bioinformatics | test_score_from_image.py | Approved | 2026-10-25 -->
