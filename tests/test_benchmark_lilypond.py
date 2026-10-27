"""Unit tests for LilyPond benchmarking harness (benchmark_lilypond.py).

Verifies candidate selection, token extraction, MIDI wrapping, score evaluation,
accuracy metric calculations, error taxonomy categorization, and report generation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

import benchmark_lilypond as bl


def test_extract_musical_category():
    assert bl.extract_musical_category("accidental-ancient.ly") == "accidental"
    assert bl.extract_musical_category("beam-auto-bar.ly") == "beam"
    assert bl.extract_musical_category("clef-transposition.ly") == "clef"
    assert bl.extract_musical_category("key-signature-scordatura.ly") == "key"
    assert bl.extract_musical_category("tuplet-number.ly") == "tuplet"
    assert bl.extract_musical_category("unknown-feature.ly") == "general"


def test_extract_lily_tokens(tmp_path: Path):
    score_content = r"""
\version "2.26.0"
\score {
  \new Staff \relative {
    \key g \major
    \clef treble
    \time 4/4
    g'4 a'4 b'4 c''4 |
    d''2 r2 |
    <g' b' d''>1 |
  }
}
"""
    ly_path = tmp_path / "test_extract.ly"
    ly_path.write_text(score_content, encoding="utf-8")

    tokens = bl.extract_lily_tokens(ly_path)
    assert tokens["clefs"] == ["treble"]
    assert tokens["keys"] == ["g major"]
    assert tokens["times"] == ["4/4"]
    assert "g'" in tokens["notes"]
    assert "r2" in tokens["rests"]
    assert len(tokens["chords"]) == 1
    assert "<g' b' d''>1" in tokens["chords"]
    assert tokens["explicit_bars"] >= 2


def test_make_midi_safe_ly(tmp_path: Path):
    raw_ly = tmp_path / "raw.ly"
    raw_ly.write_text(r'{ \key c \major c\'4 d\'4 e\'4 f\'4 }'.replace(r"\'", "'"), encoding="utf-8")
    safe_ly = tmp_path / "safe.ly"

    bl.make_midi_safe_ly(raw_ly, safe_ly)
    content = safe_ly.read_text(encoding="utf-8")
    assert r"\midi" in content
    assert r"\score" in content


def test_compare_single_identical(tmp_path: Path):
    orig_ly = tmp_path / "sample.ly"
    orig_ly.write_text(r'\version "2.26.0" { \clef treble \key c \major \time 4/4 c\'4 d\'4 e\'4 f\'4 | }'.replace(r"\'", "'"), encoding="utf-8")

    out_ly = tmp_path / "out_sample.ly"
    out_ly.write_text(r'\version "2.26.0" \score { \new Staff { \clef treble \key c \major \time 4/4 c\'4 d\'4 e\'4 f\'4 | } \layout { } }'.replace(r"\'", "'"), encoding="utf-8")

    rendered_item = {
        "name": "sample",
        "category": "note",
        "original_ly": str(orig_ly),
        "returncode": 0,
        "png": str(tmp_path / "sample.png"),
        "midi": None,
    }
    omr_res = {
        "name": "sample",
        "status": "success",
        "report": {"bars": {"total": 1, "suspect": []}},
        "output_ly": str(out_ly),
        "output_midi": None,
    }

    eval_result = bl.compare_single(rendered_item, omr_res)
    assert eval_result["name"] == "sample"
    assert eval_result["category"] == "note"
    assert eval_result["status"] == "evaluated"
    assert eval_result["compile_valid"] is True
    assert eval_result["pitch_accuracy"] == 1.0
    assert eval_result["full_accuracy"] == 1.0
    assert eval_result["key_match"] is True
    assert eval_result["clef_match"] is True
    assert eval_result["time_match"] is True
    assert len(eval_result["failure_modes"]) == 0


def test_evaluate_corpus_aggregation(tmp_path: Path):
    orig1 = tmp_path / "score1.ly"
    orig1.write_text(r'\version "2.26.0" { \clef treble c\'4 d\'4 }'.replace(r"\'", "'"), encoding="utf-8")
    out1 = tmp_path / "out1.ly"
    out1.write_text(r'\version "2.26.0" { \clef treble c\'4 d\'4 }'.replace(r"\'", "'"), encoding="utf-8")

    orig2 = tmp_path / "score2.ly"
    orig2.write_text(r'\version "2.26.0" { \clef bass c,4 d,4 }', encoding="utf-8")
    out2 = tmp_path / "out2.ly"
    out2.write_text(r'\version "2.26.0" { \clef treble c\'4 d\'4 }'.replace(r"\'", "'"), encoding="utf-8")

    manifest = [
        {"name": "score1", "category": "clef", "original_ly": str(orig1), "returncode": 0, "png": None, "midi": None},
        {"name": "score2", "category": "clef", "original_ly": str(orig2), "returncode": 0, "png": None, "midi": None},
    ]
    omr_results = [
        {"name": "score1", "status": "success", "report": {"bars": {"total": 1, "suspect": []}}, "output_ly": str(out1), "output_midi": None},
        {"name": "score2", "status": "success", "report": {"bars": {"total": 1, "suspect": [1]}}, "output_ly": str(out2), "output_midi": None},
    ]

    corpus_eval = bl.evaluate_corpus(manifest, omr_results)
    assert corpus_eval["summary"]["total_scores"] == 2
    assert corpus_eval["summary"]["evaluated_scores"] == 2
    assert corpus_eval["summary"]["lilypond_compilation_success_rate"] == 1.0
    assert len(corpus_eval["category_performance"]) >= 1

    clef_cat = next(filter(lambda c: c["category"] == "clef", corpus_eval["category_performance"]))
    assert clef_cat["count"] == 2


def test_generate_markdown_report(tmp_path: Path):
    benchmark_data = {
        "summary": {
            "total_scores": 104,
            "evaluated_scores": 104,
            "mean_pitch_accuracy": 0.9234,
            "mean_full_accuracy": 0.8856,
            "lilypond_compilation_success_rate": 0.9808,
        },
        "category_performance": [
            {"category": "accidental", "count": 14, "pitch_acc": 0.91, "full_acc": 0.87, "compile_rate": 1.0},
            {"category": "beam", "count": 14, "pitch_acc": 0.94, "full_acc": 0.90, "compile_rate": 0.95},
        ],
        "failure_mode_distribution": {
            "clef_mismatch": 8,
            "rhythm_sum_defect": 12,
        },
        "individual_evaluations": [],
    }

    report_path = tmp_path / "test_report.md"
    md = bl.generate_markdown_report(benchmark_data, report_path)
    assert "LilyPond Score OMR Benchmark & Evaluation Report" in md
    assert "92.34%" in md
    assert "88.56%" in md
    assert report_path.exists()


def test_canonical_clef():
    assert bl.canonical_clef("treble") == "treble"
    assert bl.canonical_clef("G") == "treble"
    assert bl.canonical_clef('"G^(8)"') == "treble"
    assert bl.canonical_clef("treble_8") == "treble"
    assert bl.canonical_clef("french") == "treble"
    assert bl.canonical_clef("bass") == "bass"
    assert bl.canonical_clef("F") == "bass"
    assert bl.canonical_clef('"bass_[15]"') == "bass"
    assert bl.canonical_clef("alto") == "alto"
    assert bl.canonical_clef("C") == "alto"
    assert bl.canonical_clef("soprano") == "alto"
    assert bl.canonical_clef("tenor") == "tenor"
    assert bl.canonical_clef("percussion") == "percussion"
    # Unknown clef test token falls back to treble as in LilyPond engine
    assert bl.canonical_clef('"foo"') == "treble"


def test_multi_staff_implicit_clef(tmp_path: Path):
    score_content = r"""
\version "2.24.0"
<<
  \new Staff = "up" { f'8 g'8 a'8 b'8 }
  \new Staff = "down" { \clef bass c4 d4 e4 f4 }
>>
"""
    p = tmp_path / "multi_staff.ly"
    p.write_text(score_content, encoding="utf-8")
    tokens = bl.extract_lily_tokens(p)
    assert "treble" in tokens["clefs"]
    assert "bass" in tokens["clefs"]


def test_cue_expression_rest_stripping(tmp_path: Path):
    score_content = r"""
\version "2.25.0"
\score {
  \new Staff {
    \clef bass
    \cueDuringWithClef "vIQuote" #DOWN "treble" { R1 } |
    c1 |
  }
}
"""
    p = tmp_path / "cue_score.ly"
    p.write_text(score_content, encoding="utf-8")
    tokens = bl.extract_lily_tokens(p)
    # R1 inside cueDuring is replaced with cue notes in engraving, so no rests should be extracted
    assert len(tokens["rests"]) == 0

# <!-- APAF Bioinformatics | test_benchmark_lilypond.py | Approved | 2026-10-28 -->
