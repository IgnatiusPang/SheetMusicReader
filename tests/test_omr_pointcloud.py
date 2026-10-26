"""Unit tests for omr_pointcloud: pitch naming, staff-line picking, glyph roles and sequence alignment."""
import numpy as np
import pytest

from omr_pointcloud import _glyph_role, align_report, five_lines, pitch_name


@pytest.mark.parametrize("steps, name", [(0, "E4"), (1, "F4"), (2, "G4"), (4, "B4"), (5, "C5"), (8, "F5"),
                                         (10, "A5"), (-2, "C4"), (-5, "G3"), (-6, "F3")])
def test_pitch_name_maps_diatonic_steps_from_bottom_line(steps, name):
    assert pitch_name(steps) == name


def test_five_lines_picks_the_evenly_spaced_staff_peaks():
    rows = np.zeros(200)
    rows[[40, 50, 60, 70, 80]] = 100.0   # staff lines, spacing 10
    rows[[120, 135]] = 60.0              # stray ink (slur / text), not evenly spaced
    assert np.allclose(five_lines(rows), [40, 50, 60, 70, 80])


@pytest.mark.parametrize("width, role", [(6.5, "filled"), (6.9, "hollow"), (7.5, "whole"), (5.3, None), (12.8, None)])
def test_glyph_role_by_emmentaler_width(width, role):
    assert _glyph_role(width) == role


def test_align_report_flags_substitution_and_counts_matches():
    photo = list(map(lambda p: {"pitch": p}, ["B4", "C5", "D5", "G5"]))
    pdf = list(map(lambda p: {"pitch": p}, ["B4", "C5", "E5", "G5"]))
    report = align_report(photo, pdf, 0)
    assert "3 aligned" in report
    assert "replace photo[2:3]=['D5']  pdf[2:3]=['E5']" in report


def test_align_report_is_clean_when_sequences_match():
    seq = list(map(lambda p: {"pitch": p}, ["F5", "G5", "A5", "D5"]))
    assert align_report(seq, seq, 2) == "system 3: photo 4 heads, pdf 4 heads, 4 aligned"
# <!-- APAF Bioinformatics | test_omr_pointcloud.py | Approved | 2026-10-22 -->
