"""Tests for Sing-Along WAV/MP3 synth, LilyPond PDF engraving, CLI helper, and Flask endpoints (loop-free)."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import wave
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "pdf-to-musescore" / "scripts"))

from sheet_music_reader.web import app as flask_app_mod
from sheet_music_reader.export import audio_synth
import musescore_helper
from sheet_music_reader.cli import music_pipeline
from sheet_music_reader import psalms_db
from sheet_music_reader.export import score_formatter


def _wav_duration_frames(wav_bytes: bytes) -> tuple[int, int]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        return wf.getnframes(), wf.getframerate()


def test_audio_synth_vocal_guide_and_slowdown(tmp_path: Path):
    """Vocal guide WAV renders cleanly, doubles music duration at 0.5x speed, and adds count-in frames."""
    events = (
        audio_synth.AudioEvent(0.0, 1.0, (60,), 0.9),
        audio_synth.AudioEvent(1.0, 1.0, (62,), 0.9),
        audio_synth.AudioEvent(2.0, 2.0, (64,), 0.9),
    )
    wav_full_no_ci = audio_synth.render_wav_bytes(events, "4/4", 120.0, voice="vocal_guide", count_in_bars=0)
    wav_half_no_ci = audio_synth.render_wav_bytes(events, "4/4", 60.0, voice="vocal_guide", count_in_bars=0)
    wav_half_with_ci = audio_synth.render_wav_bytes(events, "4/4", 60.0, voice="vocal_guide", count_in_bars=1)

    assert wav_full_no_ci.startswith(b"RIFF")
    assert b"WAVE" in wav_full_no_ci[:16]

    f_full, sr = _wav_duration_frames(wav_full_no_ci)
    f_half, _ = _wav_duration_frames(wav_half_no_ci)
    f_ci, _ = _wav_duration_frames(wav_half_with_ci)

    assert sr == 22050
    assert f_half > f_full * 1.7
    assert f_ci > f_half + int(3.5 * sr)

    wav_file = audio_synth.write_wav_file(tmp_path / "test_sing.wav", events, "4/4", 60.0, voice="vocal_guide")
    mp3_file = audio_synth.convert_wav_to_mp3(wav_file)
    assert mp3_file.is_file()
    assert mp3_file.stat().st_size > 1000


def test_lilypond_export_and_compile_to_pdf(tmp_path: Path):
    """GNU LilyPond exports from Psalms compile cleanly to PDF with zero syntax errors."""
    psalm = psalms_db.get_psalm("psalm_103_kind_chart")
    assert psalm is not None
    ly_text = score_formatter.export_lilypond(psalm, speed=0.5, augment=2)
    assert '\\version "2.26.0"' in ly_text
    assert "\\layout" in ly_text
    assert "\\midi" in ly_text

    ly_path = tmp_path / "psalm_103_slow_aug.ly"
    ly_path.write_text(ly_text, encoding="utf-8")
    pdf_path = music_pipeline.compile_lilypond_pdf(ly_path, tmp_path)
    assert pdf_path is not None and pdf_path.is_file()
    assert pdf_path.stat().st_size > 2000


def test_musescore_helper_lilypond_and_lean_cli(tmp_path: Path):
    """musescore_helper `slow --lilypond --lean-verify` runs cleanly and writes verified .ly files."""
    psalm = psalms_db.get_psalm("psalm_103_kind_chart")
    assert psalm is not None
    src_xml = tmp_path / "source.musicxml"
    src_xml.write_text(score_formatter.export_musicxml(psalm, speed=1.0, augment=1), encoding="utf-8")

    out_dir = tmp_path / "pack"
    rc = musescore_helper.main([
        "musescore_helper.py",
        "slow",
        str(src_xml),
        "--out", str(out_dir),
        "--speeds", "1.0,0.5",
        "--no-auto-click",
        "--lilypond",
        "--lean-verify",
    ])
    assert rc == 0
    assert (out_dir / "source_100pct.ly").is_file()
    assert (out_dir / "source_50pct.ly").is_file()
    assert (out_dir / "source_50pct.musicxml").is_file()


def test_music_pipeline_cli_convert_and_sing(tmp_path: Path):
    """music_pipeline CLI convert produces MusicXML, LilyPond, PDF, WAV, MP3, and Lean cert."""
    pdf_src = ROOT / "data" / "input" / "psalms" / "03_Ps104103-Lord-Send-Out-Your-Spirit-Chart.pdf"
    out_dir = tmp_path / "cli_out"
    rc = music_pipeline.main([
        "convert",
        str(pdf_src),
        "--out-dir", str(out_dir),
        "--speed", "0.5",
        "--voice", "vocal_guide",
        "--render-pdf",
        "--lean-cert",
    ])
    assert rc == 0
    assert any(out_dir.glob("*.musicxml"))
    assert any(out_dir.glob("*.ly"))
    assert any(out_dir.glob("*.wav"))
    assert any(out_dir.glob("*_cert.lean"))


def test_flask_new_routes_lilypond_wav_and_lean_verify():
    """Flask endpoints support `?speed=`/`?augment=`, `lilypond`, `wav`, and `/verify`."""
    flask_app_mod.app.config["TESTING"] = True
    with flask_app_mod.app.test_client() as client:
        res_ly = client.get("/api/psalms/psalm_103_kind_chart/export/lilypond?speed=0.5&augment=2")
        assert res_ly.status_code == 200
        assert b"\\version" in res_ly.data
        assert b"\\midi" in res_ly.data

        res_wav = client.get("/api/psalms/psalm_103_kind_chart/export/wav?speed=0.5&voice=vocal_guide&count_in=1")
        assert res_wav.status_code == 200
        assert res_wav.data.startswith(b"RIFF")

        res_ver = client.get("/api/psalms/psalm_103_kind_chart/verify?speed=0.5")
        assert res_ver.status_code == 200
        ver_json = res_ver.get_json()
        assert ver_json["ok"] is True
        assert ver_json["all_bars_valid"] is True
        assert ver_json["checked_bars"] >= 1


def test_karaoke_pdf_extraction_chords_lyrics_and_html(tmp_path: Path):
    """Karaoke extraction aligns Psalm 122 chords, lyrics, Je- pickup, HTML export, and Flask APIs."""
    from sheet_music_reader.karaoke import extract as karaoke_trainer

    pdf_src = ROOT / "data" / "input" / "psalms" / "04_Ps-122-I-Rejoiced-Chart.pdf"
    data = karaoke_trainer.extract_karaoke_score_from_pdf(pdf_src)
    assert data["key"] == "G Major"
    assert data["time_signature"] == "6/8"

    modes = dict(map(lambda m: (m["mode_id"], m), data["modes"]))
    assert modes["full_arrangement"]["bar_count"] == 40
    assert len(modes["full_arrangement"]["chords"]) == 50
    assert modes["chart_as_written"]["bar_count"] == 28
    assert len(modes["chart_as_written"]["chords"]) == 35
    assert tuple(map(lambda c: c["symbol"], modes["chart_as_written"]["chords"][:5])) == (
        "G",
        "F/G",
        "C",
        "D(sus4)",
        "D",
    )
    assert tuple(map(lambda w: w["text"], modes["full_arrangement"]["phrases"][0]["words"][:3])) == (
        "Let",
        "us",
        "go",
    )

    je_word = next(
        filter(lambda w: w["text"] == "Je-", modes["full_arrangement"]["phrases"][3]["words"]),
        None,
    )
    assert je_word is not None
    assert je_word["midi"] == 67
    assert je_word["pitch_name"] == "G4"

    out_html = tmp_path / "Ps_122_Karaoke_Trainer.html"
    assert music_pipeline.main(["karaoke", str(pdf_src), "--out", str(out_html)]) == 0
    assert out_html.is_file()
    html_text = out_html.read_text(encoding="utf-8")
    assert 'data-testid="active-note-pill"' in html_text
    assert "<!-- APAF Bioinformatics |" in html_text

    flask_app_mod.app.config["TESTING"] = True
    with flask_app_mod.app.test_client() as client:
        r_page = client.get("/karaoke")
        assert r_page.status_code == 200
        assert b'data-testid="active-note-pill"' in r_page.data

        r_list = client.get("/api/karaoke/list")
        assert r_list.status_code == 200
        scores = r_list.get_json()["scores"]
        assert scores
        assert "label" in scores[0]
        assert scores[0]["id"] == "pdf:04_Ps-122-I-Rejoiced-Chart.pdf"

        r_score = client.get("/api/karaoke/score/pdf:04_Ps-122-I-Rejoiced-Chart.pdf")
        assert r_score.status_code == 200
        score_json = r_score.get_json()
        assert len(score_json["modes"]) == 6


# <!-- APAF Bioinformatics | test_music_pipeline.py | Approved | 2026-11-15 -->
