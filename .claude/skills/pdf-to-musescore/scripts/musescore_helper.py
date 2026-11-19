#!/usr/bin/env python3
"""MuseScore conversion, double-check verification, and slow-practice generator for Violin & Piano.

Commands:
  inspect    Check whether a PDF is a vector score (embedded music font) or a scan/photo.
  from-repo  Convert a PDF or image in this repo into a verified MusicXML (.musicxml) file.
  verify     Double-check a MusicXML file (bar-by-bar rhythm math, violin G3 floor, piano RH/LH sync, ties, tempo).
  slow       Create slow and ultra-slow practice editions (.musicxml and .mid) for MuseScore.

Functional implementation: no imperative loops (uses map, filter, reduce, itertools).
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from fractions import Fraction
from functools import reduce
from itertools import chain
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

MUSIC_FONT_KEYWORDS = (
    "Leland", "Bravura", "MScore", "Opus", "Maestro", "Sonata",
    "Petrucci", "Engraver", "Gonville", "Emmentaler", "Sebastiano", "TTE",
)
TEXT_FONT_EXCLUSIONS = ("Text", "Chords", "Times", "Arial", "Helvetica", "Calibri")

STEP_NAMES = ("C", "D", "E", "F", "G", "A", "B")
STEP_TO_SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
FIFTHS_MAJOR_NAMES = {
    -7: "Cb Major", -6: "Gb Major", -5: "Db Major", -4: "Ab Major",
    -3: "Eb Major", -2: "Bb Major", -1: "F Major", 0: "C Major",
    1: "G Major", 2: "D Major", 3: "A Major", 4: "E Major",
    5: "B Major", 6: "F# Major", 7: "C# Major",
}
SHARP_STEPS = (3, 0, 4, 1, 5, 2, 6)
FLAT_STEPS = (6, 2, 5, 1, 4, 0, 3)

# Instrument profiles: (lowest_midi, highest_midi, gm_program_1based, display_name)
INSTRUMENT_PROFILES = {
    "violin": (55, 103, 41, "Violin"),          # Open G3 (MIDI 55) to G7 (MIDI 103)
    "piano": (21, 108, 1, "Piano"),             # A0 (MIDI 21) to C8 (MIDI 108)
}

TYPE_TABLE = (
    (Fraction(4, 1), "whole", 0),
    (Fraction(3, 1), "half", 1),
    (Fraction(7, 2), "half", 2),
    (Fraction(2, 1), "half", 0),
    (Fraction(3, 2), "quarter", 1),
    (Fraction(7, 4), "quarter", 2),
    (Fraction(1, 1), "quarter", 0),
    (Fraction(3, 4), "eighth", 1),
    (Fraction(7, 8), "eighth", 2),
    (Fraction(1, 2), "eighth", 0),
    (Fraction(3, 8), "16th", 1),
    (Fraction(1, 4), "16th", 0),
    (Fraction(1, 8), "32nd", 0),
)

MUSESCORE_CANDIDATES = (
    "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
    "/Applications/MuseScore 3.app/Contents/MacOS/mscore",
    "mscore",
    "MuseScore4",
    "MuseScore3",
)


def midi_to_note_name(midi: int) -> str:
    names = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
    return f"{names[midi % 12]}{(midi // 12) - 1}"


# ----------------------------------------------------------------------------- 1. PDF Inspection

def _fonts_from_pdffonts(pdf_path: Path) -> list[str]:
    if shutil.which("pdffonts") is None:
        return []
    res = subprocess.run(["pdffonts", str(pdf_path)], capture_output=True, text=True)
    if res.returncode != 0:
        return []
    lines = res.stdout.splitlines()[2:]
    return list(filter(None, map(lambda ln: ln.split()[0] if ln.strip() else "", lines)))


def _fonts_from_bytes(pdf_path: Path) -> list[str]:
    raw = pdf_path.read_bytes()
    matches = re.findall(rb"/(?:BaseFont|FontName)\s*/([A-Za-z0-9+_-]+)", raw)
    return sorted(set(map(lambda m: m.decode("latin1", errors="ignore"), matches)))


def is_music_font(font_name: str) -> bool:
    has_kw = any(map(lambda kw: kw.lower() in font_name.lower(), MUSIC_FONT_KEYWORDS))
    excluded = any(map(lambda ex: ex.lower() in font_name.lower(), TEXT_FONT_EXCLUSIONS))
    return has_kw and not excluded


def inspect_file(path: Path) -> dict:
    """Determine whether an input score is a vector PDF, a scanned PDF, an image, or MusicXML."""
    ext = path.suffix.lower()
    if not path.exists():
        return {"file": str(path), "error": "File not found"}
    if ext in (".musicxml", ".xml", ".mxl"):
        return {
            "file": str(path),
            "kind": "musicxml",
            "music_fonts": [],
            "all_fonts": [],
            "summary": "Already in MusicXML format. Run `verify` to double-check and `slow` to make slow practice files.",
        }
    if ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"):
        return {
            "file": str(path),
            "kind": "image_score",
            "music_fonts": [],
            "all_fonts": [],
            "summary": "Camera photo or scan of sheet music. Use optical music recognition (score_from_image.py or AI vision) followed by `verify`.",
        }
    if ext == ".pdf":
        fonts = _fonts_from_pdffonts(path) or _fonts_from_bytes(path)
        music_fonts = list(filter(is_music_font, fonts))
        kind = "vector_pdf" if music_fonts else "scanned_pdf"
        advice = (
            f"Digital vector score (music fonts: {', '.join(music_fonts)}). Notes and rhythms can be read directly with glyph accuracy."
            if music_fonts else
            "Scanned PDF (no embedded music font found). Treat pages as images at 300 DPI and run the `verify` double-check carefully."
        )
        return {
            "file": str(path),
            "kind": kind,
            "music_fonts": music_fonts,
            "all_fonts": fonts,
            "summary": advice,
        }
    return {"file": str(path), "kind": "unknown", "music_fonts": [], "all_fonts": [], "summary": f"Unrecognized file type: {ext}"}


# ----------------------------------------------------------------------------- 2. MusicXML Builder Helpers

def duration_to_xml_parts(quarters: Fraction, divisions: int = 48) -> tuple[int, str, int, tuple[int, int] | None]:
    """Return (xml_duration, type_name, dots, (actual_notes, normal_notes) or None)."""
    q = Fraction(quarters).limit_denominator(48)
    xml_dur = max(1, int(round(float(q * divisions))))
    exact = next(filter(lambda row: row[0] == q, TYPE_TABLE), None)
    if exact is not None:
        return xml_dur, exact[1], exact[2], None
    triplet_q = q * Fraction(3, 2)
    triplet_match = next(filter(lambda row: row[0] == triplet_q and row[2] == 0, TYPE_TABLE), None)
    if triplet_match is not None:
        return xml_dur, triplet_match[1], 0, (3, 2)
    duplet_q = q * Fraction(2, 3)
    duplet_match = next(filter(lambda row: row[0] == duplet_q and row[2] == 0, TYPE_TABLE), None)
    if duplet_match is not None:
        return xml_dur, duplet_match[1], 0, (2, 3)
    nearest = min(TYPE_TABLE, key=lambda row: abs(float(row[0] - q)))
    return xml_dur, nearest[1], nearest[2], None


def clef_to_xml_sign_line(clef_name: str) -> tuple[str, str, int]:
    clean = clef_name.strip().strip('"')
    mapping = {
        "G": ("G", "2", 0), "treble": ("G", "2", 0),
        "G8vb": ("G", "2", -1), "treble_8": ("G", "2", -1),
        "G8va": ("G", "2", 1), "treble^8": ("G", "2", 1),
        "F": ("F", "4", 0), "bass": ("F", "4", 0), "bass_8": ("F", "4", -1),
        "C": ("C", "3", 0), "alto": ("C", "3", 0), "tenor": ("C", "4", 0),
    }
    return mapping.get(clean, ("G", "2", 0))


def _ensure_child(parent: ET.Element, tag: str, **attrib) -> ET.Element:
    found = parent.find(tag)
    return found if found is not None else ET.SubElement(parent, tag, **attrib)


def _attach_midi_instrument(score_part_el: ET.Element, part_id: str, instrument: str) -> None:
    profile = INSTRUMENT_PROFILES.get(instrument.lower())
    if not profile:
        return
    _, _, gm_prog, disp_name = profile
    inst_id = f"{part_id}-I1"
    si = _ensure_child(score_part_el, "score-instrument", id=inst_id)
    si.attrib["id"] = inst_id
    iname = _ensure_child(si, "instrument-name")
    iname.text = disp_name
    mi = _ensure_child(score_part_el, "midi-instrument", id=inst_id)
    mi.attrib["id"] = inst_id
    mp = _ensure_child(mi, "midi-program")
    mp.text = str(gm_prog)


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    pad = "\n" + level * "  "
    children = list(elem)
    if children:
        if not elem.text or not elem.text.strip():
            elem.text = pad + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = pad
        list(map(lambda c: _indent_xml(c, level + 1), children))
        if not children[-1].tail or not children[-1].tail.strip():
            children[-1].tail = pad
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = pad


def serialize_score_partwise(root: ET.Element) -> str:
    _indent_xml(root)
    body = ET.tostring(root, encoding="unicode")
    header = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">\n'
    )
    return header + body + "\n"


def vector_score_to_musicxml(score, title: str | None = None, instrument: str = "auto") -> str:
    """Convert a vector_omr.Score object into standard MusicXML 3.1 for MuseScore."""
    divisions = 48
    work_title = title or Path(score.path).stem.replace("_", " ").replace("-", " ")
    tempo_bpm = int(round(float(getattr(score, "tempo", 90.0) or 90.0)))
    n_lanes = max(map(len, score.systems)) if score.systems else 1
    inst_mode = ("piano" if n_lanes >= 2 else "violin") if instrument == "auto" else instrument

    root = ET.Element("score-partwise", version="3.1")
    work = ET.SubElement(root, "work")
    ET.SubElement(work, "work-title").text = work_title
    part_list = ET.SubElement(root, "part-list")

    def add_part_header(lane_idx: int) -> None:
        pid = f"P{lane_idx + 1}"
        sp = ET.SubElement(part_list, "score-part", id=pid)
        default_name = (
            "Violin" if (inst_mode == "violin" and n_lanes == 1) else
            ("Piano Right Hand" if lane_idx == 0 else "Piano Left Hand") if (inst_mode == "piano" and n_lanes == 2) else
            ("Melody" if lane_idx == 0 else f"Staff {lane_idx + 1}")
        )
        ET.SubElement(sp, "part-name").text = default_name
        _attach_midi_instrument(sp, pid, "violin" if (inst_mode == "violin" and lane_idx == 0) else "piano")

    list(map(add_part_header, range(n_lanes)))

    def build_part(lane_idx: int) -> None:
        part_el = ET.SubElement(root, "part", id=f"P{lane_idx + 1}")
        measures = list(chain.from_iterable(map(
            lambda sys_staves: sys_staves[lane_idx].measures if lane_idx < len(sys_staves) else (),
            score.systems,
        )))

        def step_measure(state: tuple, idx_m: tuple) -> tuple:
            prev_key, prev_time, prev_clef, open_ties = state
            m_idx, m = idx_m
            m_el = ET.SubElement(part_el, "measure", number=str(m_idx + 1))
            need_attr = (m_idx == 0) or (m.key != prev_key) or (m.time != prev_time) or (m.clef != prev_clef)
            if need_attr:
                attr = ET.SubElement(m_el, "attributes")
                if m_idx == 0:
                    ET.SubElement(attr, "divisions").text = str(divisions)
                if m_idx == 0 or m.key != prev_key:
                    k_el = ET.SubElement(attr, "key")
                    ET.SubElement(k_el, "fifths").text = str(m.key)
                if m_idx == 0 or m.time != prev_time:
                    t_el = ET.SubElement(attr, "time")
                    ET.SubElement(t_el, "beats").text = str(m.time[0])
                    ET.SubElement(t_el, "beat-type").text = str(m.time[1])
                if m_idx == 0 or m.clef != prev_clef:
                    c_el = ET.SubElement(attr, "clef")
                    sign, line, oct_ch = clef_to_xml_sign_line(m.clef)
                    ET.SubElement(c_el, "sign").text = sign
                    ET.SubElement(c_el, "line").text = line
                    if oct_ch != 0:
                        ET.SubElement(c_el, "clef-octave-change").text = str(oct_ch)
            if m_idx == 0 and lane_idx == 0:
                direction = ET.SubElement(m_el, "direction", placement="above")
                dt = ET.SubElement(direction, "direction-type")
                met = ET.SubElement(dt, "metronome")
                ET.SubElement(met, "beat-unit").text = "quarter"
                ET.SubElement(met, "per-minute").text = str(tempo_bpm)
                ET.SubElement(direction, "sound", tempo=str(tempo_bpm))

            regular_events = tuple(filter(lambda e: not getattr(e, "extra", False), m.events))

            def emit_event(ties_in: set, ev) -> set:
                xml_dur, type_name, dots, tuplet = duration_to_xml_parts(Fraction(ev.value).limit_denominator(48), divisions)
                if not ev.heads:
                    n_el = ET.SubElement(m_el, "note")
                    ET.SubElement(n_el, "rest")
                    ET.SubElement(n_el, "duration").text = str(xml_dur)
                    ET.SubElement(n_el, "voice").text = "1"
                    ET.SubElement(n_el, "type").text = type_name
                    list(map(lambda _: ET.SubElement(n_el, "dot"), range(dots)))
                    return set()
                sorted_heads = sorted(ev.heads, key=lambda h: h.midi)

                def emit_head(idx_h: tuple) -> int:
                    h_idx, h = idx_h
                    n_el = ET.SubElement(m_el, "note")
                    if h_idx > 0:
                        ET.SubElement(n_el, "chord")
                    step_idx = h.d % 7
                    step_name = STEP_NAMES[step_idx]
                    octv = h.d // 7
                    natural_midi = (octv + 1) * 12 + STEP_TO_SEMI[step_name]
                    alter = h.midi - natural_midi
                    if alter > 2 or alter < -2:
                        octv = (h.midi // 12) - 1
                        rem = h.midi % 12
                        near_step = min(range(7), key=lambda s_i: abs(STEP_TO_SEMI[STEP_NAMES[s_i]] - rem))
                        step_name = STEP_NAMES[near_step]
                        alter = rem - STEP_TO_SEMI[step_name]
                    p_el = ET.SubElement(n_el, "pitch")
                    ET.SubElement(p_el, "step").text = step_name
                    if alter != 0:
                        ET.SubElement(p_el, "alter").text = str(alter)
                    ET.SubElement(p_el, "octave").text = str(octv)
                    ET.SubElement(n_el, "duration").text = str(xml_dur)
                    tie_stop = h.midi in ties_in
                    tie_start = bool(ev.tie)
                    if tie_stop:
                        ET.SubElement(n_el, "tie", type="stop")
                    if tie_start:
                        ET.SubElement(n_el, "tie", type="start")
                    ET.SubElement(n_el, "voice").text = "1"
                    ET.SubElement(n_el, "type").text = type_name
                    list(map(lambda _: ET.SubElement(n_el, "dot"), range(dots)))
                    if tuplet is not None:
                        tm = ET.SubElement(n_el, "time-modification")
                        ET.SubElement(tm, "actual-notes").text = str(tuplet[0])
                        ET.SubElement(tm, "normal-notes").text = str(tuplet[1])
                    if tie_stop or tie_start:
                        notations = ET.SubElement(n_el, "notations")
                        if tie_stop:
                            ET.SubElement(notations, "tied", type="stop")
                        if tie_start:
                            ET.SubElement(notations, "tied", type="start")
                    return h.midi

                sounding = set(map(emit_head, enumerate(sorted_heads)))
                return sounding if ev.tie else set()

            next_ties = reduce(emit_event, regular_events, open_ties)
            return (m.key, m.time, m.clef, next_ties)

        reduce(step_measure, enumerate(measures), (None, None, None, set()))

    list(map(build_part, range(n_lanes)))
    return serialize_score_partwise(root)


def image_score_to_musicxml(score, instrument: str = "auto") -> str:
    """Convert a score_from_image.Score object into standard MusicXML 3.1 for MuseScore."""
    from sheet_music_reader.omr import score_from_image as sfi
    divisions = 48
    work_title = score.title or "Score"
    tempo_bpm = int(score.tempo[1]) if score.tempo else 90
    n_parts = len(score.parts)
    inst_mode = ("piano" if n_parts >= 2 else "violin") if instrument == "auto" else instrument

    root = ET.Element("score-partwise", version="3.1")
    work = ET.SubElement(root, "work")
    ET.SubElement(work, "work-title").text = work_title
    if score.composer:
        ident = ET.SubElement(root, "identification")
        creator = ET.SubElement(ident, "creator", type="composer")
        creator.text = score.composer
    part_list = ET.SubElement(root, "part-list")

    def add_part_header(idx: int) -> None:
        pid = f"P{idx + 1}"
        sp = ET.SubElement(part_list, "score-part", id=pid)
        pname = (
            "Violin" if (inst_mode == "violin" and n_parts == 1) else
            ("Piano Right Hand" if idx == 0 else "Piano Left Hand") if (inst_mode == "piano" and n_parts == 2) else
            f"Part {idx + 1}"
        )
        ET.SubElement(sp, "part-name").text = pname
        _attach_midi_instrument(sp, pid, "violin" if (inst_mode == "violin" and idx == 0) else "piano")

    list(map(add_part_header, range(n_parts)))

    def build_part(p_idx: int) -> None:
        part = score.parts[p_idx]
        part_el = ET.SubElement(root, "part", id=f"P{p_idx + 1}")

        def emit_bar(open_ties: set, b_idx_bar: tuple) -> set:
            b_idx, bar = b_idx_bar
            m_el = ET.SubElement(part_el, "measure", number=str(b_idx + 1))
            time_change = next(filter(lambda c: c.startswith("\\time "), bar.changes), None)
            clef_change = next(filter(lambda c: c.startswith("\\clef "), bar.changes), None)
            if b_idx == 0 or time_change or clef_change:
                attr = ET.SubElement(m_el, "attributes")
                if b_idx == 0:
                    ET.SubElement(attr, "divisions").text = str(divisions)
                    k_el = ET.SubElement(attr, "key")
                    ET.SubElement(k_el, "fifths").text = str(score.key[0])
                    ET.SubElement(k_el, "mode").text = score.key[1]
                if b_idx == 0 or time_change:
                    num, den = (map(int, time_change.split()[1].split("/")) if time_change else score.time)
                    t_el = ET.SubElement(attr, "time")
                    ET.SubElement(t_el, "beats").text = str(num)
                    ET.SubElement(t_el, "beat-type").text = str(den)
                if b_idx == 0 or clef_change:
                    c_name = clef_change.split(None, 1)[1] if clef_change else part.clef
                    sign, line, oct_ch = clef_to_xml_sign_line(c_name)
                    c_el = ET.SubElement(attr, "clef")
                    ET.SubElement(c_el, "sign").text = sign
                    ET.SubElement(c_el, "line").text = line
                    if oct_ch != 0:
                        ET.SubElement(c_el, "clef-octave-change").text = str(oct_ch)
            if b_idx == 0 and p_idx == 0:
                direction = ET.SubElement(m_el, "direction", placement="above")
                dt = ET.SubElement(direction, "direction-type")
                if score.tempo_text:
                    ET.SubElement(dt, "words").text = score.tempo_text
                met = ET.SubElement(dt, "metronome")
                ET.SubElement(met, "beat-unit").text = "quarter"
                ET.SubElement(met, "per-minute").text = str(tempo_bpm)
                ET.SubElement(direction, "sound", tempo=str(tempo_bpm))

            def emit_ev(ties_in: set, ev) -> set:
                xml_dur, type_name, dots, tuplet = duration_to_xml_parts(ev.dur, divisions)
                dyn_marks = tuple(filter(lambda mk: mk.lstrip("\\") in sfi.DYNAMICS, ev.marks))
                list(map(
                    lambda dm: ET.SubElement(
                        ET.SubElement(ET.SubElement(m_el, "direction", placement="below"), "direction-type"),
                        "dynamics",
                    ).append(ET.Element(dm.lstrip("\\"))),
                    dyn_marks,
                ))
                if not ev.pitches:
                    n_el = ET.SubElement(m_el, "note")
                    ET.SubElement(n_el, "rest")
                    ET.SubElement(n_el, "duration").text = str(xml_dur)
                    ET.SubElement(n_el, "voice").text = "1"
                    ET.SubElement(n_el, "type").text = type_name
                    list(map(lambda _: ET.SubElement(n_el, "dot"), range(dots)))
                    return set()

                def emit_pitch(idx_p: tuple) -> str:
                    h_idx, lp = idx_p
                    m_match = sfi.PITCH_RE.match(lp)
                    step_l, acc_s, oct_s = m_match.groups()
                    step_u = step_l.upper()
                    alter = sfi.NAME_ALTER[acc_s or ""]
                    octave = 3 + oct_s.count("'") - oct_s.count(",")
                    n_el = ET.SubElement(m_el, "note")
                    if ev.grace:
                        ET.SubElement(n_el, "grace", slash="yes")
                    if h_idx > 0:
                        ET.SubElement(n_el, "chord")
                    p_el = ET.SubElement(n_el, "pitch")
                    ET.SubElement(p_el, "step").text = step_u
                    if alter != 0:
                        ET.SubElement(p_el, "alter").text = str(alter)
                    ET.SubElement(p_el, "octave").text = str(octave)
                    if not ev.grace:
                        ET.SubElement(n_el, "duration").text = str(xml_dur)
                    tie_stop = lp in ties_in
                    tie_start = bool(ev.tie)
                    if tie_stop:
                        ET.SubElement(n_el, "tie", type="stop")
                    if tie_start:
                        ET.SubElement(n_el, "tie", type="start")
                    ET.SubElement(n_el, "voice").text = "1"
                    ET.SubElement(n_el, "type").text = type_name
                    list(map(lambda _: ET.SubElement(n_el, "dot"), range(dots)))
                    if tuplet is not None:
                        tm = ET.SubElement(n_el, "time-modification")
                        ET.SubElement(tm, "actual-notes").text = str(tuplet[0])
                        ET.SubElement(tm, "normal-notes").text = str(tuplet[1])
                    has_slur_start = "(" in ev.marks and h_idx == 0
                    has_slur_stop = ")" in ev.marks and h_idx == 0
                    has_upbow = "\\upbow" in ev.marks and h_idx == 0
                    has_downbow = "\\downbow" in ev.marks and h_idx == 0
                    has_fermata = "\\fermata" in ev.marks and h_idx == 0
                    finger = next(filter(lambda mk: sfi.FINGER_RE.match(mk), ev.marks), None) if h_idx == 0 else None
                    if any((tie_stop, tie_start, has_slur_start, has_slur_stop, has_upbow, has_downbow, has_fermata, finger)):
                        notations = ET.SubElement(n_el, "notations")
                        if tie_stop:
                            ET.SubElement(notations, "tied", type="stop")
                        if tie_start:
                            ET.SubElement(notations, "tied", type="start")
                        if has_slur_stop:
                            ET.SubElement(notations, "slur", type="stop", number="1")
                        if has_slur_start:
                            ET.SubElement(notations, "slur", type="start", number="1")
                        if has_upbow or has_downbow or finger:
                            tech = ET.SubElement(notations, "technical")
                            if has_upbow:
                                ET.SubElement(tech, "up-bow")
                            if has_downbow:
                                ET.SubElement(tech, "down-bow")
                            if finger:
                                ET.SubElement(tech, "fingering").text = finger.lstrip("-")
                        if has_fermata:
                            ET.SubElement(notations, "fermata", type="upright")
                    return lp

                sounding = set(map(emit_pitch, enumerate(ev.pitches)))
                return sounding if ev.tie else set()

            return reduce(emit_ev, bar.events, open_ties)

        reduce(emit_bar, enumerate(part.bars), set())

    list(map(build_part, range(n_parts)))
    return serialize_score_partwise(root)


# ----------------------------------------------------------------------------- 3. Double-Check Verification Engine

@dataclass(frozen=True)
class NoteEvent:
    measure: str
    voice: str
    staff: str
    midi: int | None          # None for rest
    quarters: Fraction
    tie_start: bool = False
    tie_stop: bool = False
    is_chord: bool = False
    is_grace: bool = False


def _pitch_el_to_midi(pitch_el: ET.Element) -> int:
    step = (pitch_el.findtext("step") or "C").strip().upper()
    alter = int(float(pitch_el.findtext("alter") or "0"))
    octave = int(pitch_el.findtext("octave") or "4")
    return (octave + 1) * 12 + STEP_TO_SEMI.get(step, 0) + alter


def _detect_instrument(root: ET.Element, requested: str) -> str:
    if requested in ("violin", "piano"):
        return requested
    part_names = " ".join(map(lambda el: (el.text or "").lower(), root.findall(".//part-name") + root.findall(".//instrument-name")))
    if "violin" in part_names or "vln" in part_names:
        return "violin"
    if "piano" in part_names or len(root.findall("part")) >= 2 or root.find(".//staves") is not None:
        return "piano"
    return "violin" if len(root.findall("part")) == 1 else "piano"


def verify_musicxml(path: Path, reference_path: Path | None = None, instrument: str = "auto") -> dict:
    """Perform a thorough structural, mathematical, and violin/piano musical double-check on a MusicXML file."""
    tree = ET.parse(path)
    root = tree.getroot()
    title = (
        root.findtext("./work/work-title")
        or root.findtext("./movement-title")
        or path.stem
    )
    detected_inst = _detect_instrument(root, instrument)
    parts = root.findall("part")
    sound_tempos = list(map(
        lambda s: float(s.attrib["tempo"]),
        filter(lambda s: "tempo" in s.attrib, root.findall(".//sound")),
    ))
    metronome_tempos = list(map(
        lambda pm: float(pm.text.strip()),
        filter(lambda pm: pm.text and pm.text.strip().replace(".", "", 1).isdigit(), root.findall(".//metronome/per-minute")),
    ))

    def audit_part(p_idx_el: tuple) -> dict:
        p_idx, part_el = p_idx_el
        part_id = part_el.attrib.get("id", f"P{p_idx + 1}")
        measures = part_el.findall("measure")
        n_measures = len(measures)
        is_violin_part = (detected_inst == "violin" and p_idx == 0)
        low_midi, high_midi = INSTRUMENT_PROFILES["violin" if is_violin_part else "piano"][:2]

        def step_measure(state: dict, idx_m: tuple) -> dict:
            m_idx, m_el = idx_m
            m_num = m_el.attrib.get("number", str(m_idx + 1))
            attr = m_el.find("attributes")
            div = int(attr.findtext("divisions")) if attr is not None and attr.findtext("divisions") else state["div"]
            beats_txt = attr.findtext("./time/beats") if attr is not None else None
            btype_txt = attr.findtext("./time/beat-type") if attr is not None else None
            time_sig = (int(beats_txt), int(btype_txt)) if (beats_txt and btype_txt) else state["time"]
            fifths_txt = attr.findtext("./key/fifths") if attr is not None else None
            fifths = int(fifths_txt) if fifths_txt is not None else state["fifths"]
            clef_sign = attr.findtext("./clef/sign") if attr is not None else None
            clef = clef_sign if clef_sign is not None else state["clef"]

            expected_q = Fraction(time_sig[0] * 4, time_sig[1])

            def proc_child(m_state: tuple, child: ET.Element) -> tuple:
                pos_q, max_pos_q, voice_sums, notes_acc, open_ties, tie_errors = m_state
                tag = child.tag
                if tag == "backup":
                    d = int(child.findtext("duration") or "0")
                    return (pos_q - Fraction(d, div), max_pos_q, voice_sums, notes_acc, open_ties, tie_errors)
                if tag == "forward":
                    d = int(child.findtext("duration") or "0")
                    new_p = pos_q + Fraction(d, div)
                    return (new_p, max(max_pos_q, new_p), voice_sums, notes_acc, open_ties, tie_errors)
                if tag != "note":
                    return m_state
                is_grace = child.find("grace") is not None
                is_chord = child.find("chord") is not None
                is_rest = child.find("rest") is not None
                dur_ticks = 0 if is_grace else int(child.findtext("duration") or "0")
                dur_q = Fraction(dur_ticks, div)
                voice = (child.findtext("voice") or "1").strip()
                staff_num = (child.findtext("staff") or "1").strip()
                pitch_el = child.find("pitch")
                midi = None if (is_rest or pitch_el is None) else _pitch_el_to_midi(pitch_el)
                tie_types = set(map(lambda t: t.attrib.get("type", ""), child.findall("tie") + child.findall("./notations/tied")))
                t_start = "start" in tie_types
                t_stop = "stop" in tie_types

                new_tie_errs = list(tie_errors)
                next_ties = set(open_ties)
                tie_key = (staff_num, midi)
                if midi is not None:
                    if t_stop and tie_key not in next_ties:
                        new_tie_errs.append(f"Bar {m_num}: tie stop on {midi_to_note_name(midi)} (MIDI {midi}) without matching tie start")
                    if t_stop and tie_key in next_ties:
                        next_ties.discard(tie_key)
                    if t_start:
                        next_ties.add(tie_key)

                new_pos = pos_q if (is_chord or is_grace) else pos_q + dur_q
                new_max = max(max_pos_q, new_pos)
                prev_v = voice_sums.get(voice, Fraction(0))
                new_v_sums = {**voice_sums, voice: prev_v if (is_chord or is_grace) else prev_v + dur_q}
                ev = NoteEvent(m_num, voice, staff_num, midi, dur_q, t_start, t_stop, is_chord, is_grace)
                return (new_pos, new_max, new_v_sums, notes_acc + [ev], next_ties, new_tie_errs)

            _, max_q, v_sums, m_notes, next_ties, tie_errs = reduce(
                proc_child, list(m_el), (Fraction(0), Fraction(0), {}, [], state["open_ties"], []),
            )
            bar_q = v_sums.get("1", max_q)
            is_first = m_idx == 0
            is_last = m_idx == n_measures - 1
            status = (
                "OK" if bar_q == expected_q else
                "PICKUP" if (is_first and Fraction(0) < bar_q < expected_q) else
                "CLOSING" if (is_last and Fraction(0) < bar_q < expected_q) else
                "EMPTY" if bar_q == 0 else
                "SUSPECT_SHORT" if bar_q < expected_q else
                "SUSPECT_OVER"
            )
            bar_rec = {
                "bar": m_num,
                "index": m_idx + 1,
                "status": status,
                "got_beats": float(bar_q),
                "expected_beats": float(expected_q),
                "got_fraction": str(bar_q),
                "expected_fraction": str(expected_q),
                "diff_beats": float(bar_q - expected_q),
                "time_signature": f"{time_sig[0]}/{time_sig[1]}",
            }
            return {
                "div": div,
                "time": time_sig,
                "fifths": fifths,
                "clef": clef,
                "open_ties": next_ties,
                "bars": state["bars"] + [bar_rec],
                "notes": state["notes"] + m_notes,
                "tie_errors": state["tie_errors"] + tie_errs,
            }

        final_state = reduce(
            step_measure,
            enumerate(measures),
            {"div": 1, "time": (4, 4), "fifths": 0, "clef": "G", "open_ties": set(), "bars": [], "notes": [], "tie_errors": []},
        )
        dangling = list(map(
            lambda sm: f"Unclosed tie at end of part on {midi_to_note_name(sm[1])} (MIDI {sm[1]})",
            sorted(final_state["open_ties"]),
        ))
        pitched = list(filter(lambda n: n.midi is not None and not n.is_chord and not n.is_grace, final_state["notes"]))
        out_of_range = list(map(
            lambda n: (
                f"Bar {n.measure}: note {midi_to_note_name(n.midi)} (MIDI {n.midi}) is below the violin's lowest string (open G3, MIDI 55)!"
                if (is_violin_part and n.midi < 55) else
                f"Bar {n.measure}: extreme pitch {midi_to_note_name(n.midi)} (MIDI {n.midi}) outside normal {detected_inst} range"
            ),
            filter(lambda n: n.midi < low_midi or n.midi > high_midi, pitched),
        ))
        leaps = list(map(
            lambda pair: (
                f"Bar {pair[1].measure}: huge pitch leap of {abs(pair[1].midi - pair[0].midi)} semitones "
                f"({midi_to_note_name(pair[0].midi)} -> {midi_to_note_name(pair[1].midi)}); check for a stray speck or wrong clef"
            ),
            filter(lambda pair: pair[0].staff == pair[1].staff and abs(pair[1].midi - pair[0].midi) > 36, zip(pitched, pitched[1:])),
        ))
        suspects = list(filter(lambda b: b["status"].startswith("SUSPECT") or b["status"] == "EMPTY", final_state["bars"]))
        return {
            "part_id": part_id,
            "measures": len(measures),
            "notes": len(pitched),
            "key_fifths": final_state["fifths"],
            "key_name": FIFTHS_MAJOR_NAMES.get(final_state["fifths"], f"{final_state['fifths']} fifths"),
            "time_signature": f"{final_state['time'][0]}/{final_state['time'][1]}",
            "clef": final_state["clef"],
            "full_bars": len(list(filter(lambda b: b["status"] == "OK", final_state["bars"]))),
            "pickup_or_closing": len(list(filter(lambda b: b["status"] in ("PICKUP", "CLOSING"), final_state["bars"]))),
            "suspect_bars": suspects,
            "tie_errors": final_state["tie_errors"] + dangling,
            "pitch_warnings": out_of_range + leaps,
            "bar_details": final_state["bars"],
        }

    part_reports = list(map(audit_part, enumerate(parts)))
    all_suspects = list(chain.from_iterable(map(
        lambda pr: list(map(lambda sb: {**sb, "part": pr["part_id"]}, pr["suspect_bars"])),
        part_reports,
    )))
    all_tie_errors = list(chain.from_iterable(map(lambda pr: pr["tie_errors"], part_reports)))
    all_pitch_warnings = list(chain.from_iterable(map(lambda pr: pr["pitch_warnings"], part_reports)))

    # Piano / multi-part bar count synchronization check
    bar_counts = sorted(set(map(lambda pr: pr["measures"], part_reports)))
    sync_errors = (
        [f"Hand/Part bar count mismatch: parts have {list(map(lambda pr: (pr['part_id'], pr['measures']), part_reports))} bars! Right and Left hands will drift out of sync."]
        if len(bar_counts) > 1 else []
    )

    tempo_mismatch = (
        bool(sound_tempos and metronome_tempos)
        and abs(sound_tempos[0] - metronome_tempos[0]) > 1.5
    )
    tempo_warnings = (
        [f"Visible metronome ({metronome_tempos[0]:g} BPM) differs from playback sound tempo ({sound_tempos[0]:g} BPM)"]
        if tempo_mismatch else
        (["No tempo marking found; MuseScore will default to 120 BPM unless set."] if not (sound_tempos or metronome_tempos) else [])
    )

    ref_comparison = None
    if reference_path is not None and reference_path.exists():
        seq_a = extract_sounding_sequence(path)
        seq_b = extract_sounding_sequence(reference_path)
        pitches_a = list(map(lambda x: x[0], seq_a))
        pitches_b = list(map(lambda x: x[0], seq_b))
        import difflib
        pitch_hits = sum(map(lambda blk: blk.size, difflib.SequenceMatcher(a=pitches_b, b=pitches_a, autojunk=False).get_matching_blocks()))
        both_hits = sum(map(lambda blk: blk.size, difflib.SequenceMatcher(a=seq_b, b=seq_a, autojunk=False).get_matching_blocks()))
        denom = max(1, len(seq_b))
        ref_comparison = {
            "reference": str(reference_path),
            "test_notes": len(seq_a),
            "reference_notes": len(seq_b),
            "pitch_accuracy": round(pitch_hits / denom, 4),
            "rhythm_and_pitch_accuracy": round(both_hits / denom, 4),
        }

    passed = (len(all_suspects) == 0) and (len(all_tie_errors) == 0) and (len(sync_errors) == 0) and not tempo_mismatch
    return {
        "file": str(path),
        "title": title,
        "instrument": detected_inst,
        "passed": passed,
        "status": "PASS" if passed else "NEEDS_REVIEW",
        "tempo_bpm": sound_tempos[0] if sound_tempos else (metronome_tempos[0] if metronome_tempos else None),
        "parts": part_reports,
        "suspect_bars": all_suspects,
        "sync_errors": sync_errors,
        "tie_errors": all_tie_errors,
        "pitch_warnings": all_pitch_warnings,
        "tempo_warnings": tempo_warnings,
        "reference_comparison": ref_comparison,
    }


def extract_sounding_sequence(path: Path, part_index: int = 0) -> list[tuple[int, Fraction]]:
    """Extract (midi_pitch, duration_in_quarters) of part `part_index` (voice 1), merging tied notes."""
    ext = path.suffix.lower()
    if ext in (".mid", ".midi"):
        return _midi_sounding_sequence(path, track_index=part_index)
    tree = ET.parse(path)
    root = tree.getroot()
    parts = root.findall("part")
    if part_index >= len(parts):
        return []
    measures = parts[part_index].findall("measure")

    def collect_measure(state: tuple, m_el: ET.Element) -> tuple:
        div, acc = state
        attr = m_el.find("attributes")
        new_div = int(attr.findtext("divisions")) if attr is not None and attr.findtext("divisions") else div

        def collect_note(notes_list: list, n_el: ET.Element) -> list:
            if n_el.find("grace") is not None or n_el.find("rest") is not None:
                return notes_list
            voice = (n_el.findtext("voice") or "1").strip()
            if voice != "1":
                return notes_list
            pitch_el = n_el.find("pitch")
            if pitch_el is None:
                return notes_list
            midi = _pitch_el_to_midi(pitch_el)
            dur_q = Fraction(int(n_el.findtext("duration") or "0"), new_div).limit_denominator(48)
            tie_types = set(map(lambda t: t.attrib.get("type", ""), n_el.findall("tie") + n_el.findall("./notations/tied")))
            is_chord = n_el.find("chord") is not None
            if is_chord and notes_list:
                prev_midi, prev_dur, prev_tie = notes_list[-1]
                return notes_list[:-1] + [(max(prev_midi, midi), prev_dur, prev_tie or ("start" in tie_types))]
            if "stop" in tie_types and notes_list and notes_list[-1][0] == midi:
                prev_midi, prev_dur, _ = notes_list[-1]
                return notes_list[:-1] + [(prev_midi, prev_dur + dur_q, "start" in tie_types)]
            return notes_list + [(midi, dur_q, "start" in tie_types)]

        return (new_div, reduce(collect_note, m_el.findall("note"), acc))

    _, raw_notes = reduce(collect_measure, measures, (1, []))
    return list(map(lambda item: (item[0], item[1]), raw_notes))


def _midi_sounding_sequence(path: Path, track_index: int = 0) -> list[tuple[int, Fraction]]:
    import mido
    mf = mido.MidiFile(str(path))
    if track_index >= len(mf.tracks):
        return []

    def step(acc: tuple, msg) -> tuple:
        t, active, notes = acc
        t += msg.time
        on = msg.type == "note_on" and msg.velocity > 0
        off = msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0)
        if on:
            return (t, {**active, msg.note: t}, notes)
        if off and msg.note in active:
            start = active[msg.note]
            rest = dict(filter(lambda kv: kv[0] != msg.note, active.items()))
            return (t, rest, notes + [(msg.note, Fraction(t - start, mf.ticks_per_beat).limit_denominator(48))])
        return (t, active, notes)

    return reduce(step, mf.tracks[track_index], (0, {}, []))[2]


def format_verification_report(report: dict) -> str:
    """Format the verification result as a clear, friendly checklist for a violin/piano teacher and AI."""
    inst = report.get("instrument", "violin").capitalize()
    header = [
        f"=== Double-Check Report: {report['title']} ({Path(report['file']).name}) ===",
        f"Instrument     : {inst}",
        f"Overall Status : {report['status']}",
        f"Tempo (BPM)    : {report['tempo_bpm'] if report['tempo_bpm'] is not None else 'Unmarked (defaults to 120)'}",
    ]
    part_lines = list(map(
        lambda pr: (
            f"  Part {pr['part_id']}: {pr['measures']} bars | {pr['notes']} notes | "
            f"Key: {pr['key_name']} | Time: {pr['time_signature']} | Clef: {pr['clef']} | "
            f"Full bars: {pr['full_bars']} | Pickup/Closing: {pr['pickup_or_closing']} | "
            f"Suspect: {len(pr['suspect_bars'])}"
        ),
        report["parts"],
    ))
    suspect_lines = (
        ["\nBars Needing Attention (Rhythm Math Mismatch):"] + list(map(
            lambda s: (
                f"  - [Part {s['part']}, Bar {s['bar']}] {s['status']}: "
                f"has {s['got_beats']:g} beats, expected {s['expected_beats']:g} beats in {s['time_signature']} "
                f"({s['diff_beats']:+g} beats). Check for a misread note value, missing dot, or rest."
            ),
            report["suspect_bars"],
        ))
        if report["suspect_bars"] else
        ["\nBar-by-Bar Rhythm Math: All interior bars add up to the time signature."]
    )
    sync_lines = (
        ["\nPiano Hand Synchronization Errors:"] + list(map(lambda e: f"  - {e}", report.get("sync_errors", [])))
        if report.get("sync_errors") else []
    )
    tie_lines = (
        ["\nTie Check Issues:"] + list(map(lambda e: f"  - {e}", report["tie_errors"]))
        if report["tie_errors"] else []
    )
    pitch_lines = (
        ["\nPitch & Instrument Range Warnings:"] + list(map(lambda w: f"  - {w}", report["pitch_warnings"]))
        if report["pitch_warnings"] else []
    )
    tempo_lines = (
        ["\nTempo Warnings:"] + list(map(lambda w: f"  - {w}", report["tempo_warnings"]))
        if report["tempo_warnings"] else []
    )
    ref_lines = (
        [
            "\nReference Comparison:",
            f"  - Pitch accuracy       : {report['reference_comparison']['pitch_accuracy'] * 100:.1f}%",
            f"  - Pitch + rhythm match : {report['reference_comparison']['rhythm_and_pitch_accuracy'] * 100:.1f}%",
        ]
        if report.get("reference_comparison") else []
    )
    inst_check = (
        "  [ ] 4. Violin Details: Check bowings (down-bow / up-bow), slurs vs. ties, fingerings (0-4), and open G3 floor."
        if report.get("instrument") == "violin" else
        "  [ ] 4. Piano Details: Check Left-Hand clef changes (bass <-> treble), chord stacks, and RH/LH bar alignment."
    )
    checklist = [
        f"\n5-Point {inst} Teacher & AI Visual Double-Check:",
        "  [ ] 1. Key & Time Signature: Check Bar 1 in MuseScore against the PDF (count the sharps or flats).",
        "  [ ] 2. Suspect Bars: Inspect every bar listed under 'Bars Needing Attention' above (target: 0 suspect bars).",
        "  [ ] 3. First & Last Note of Each Line: Confirm no line break skipped a bar or shifted an octave.",
        inst_check,
        "  [ ] 5. Listen at Slow Speed: Press Spacebar in MuseScore and follow the PDF with your finger.",
    ]
    return "\n".join(header + part_lines + suspect_lines + sync_lines + tie_lines + pitch_lines + tempo_lines + ref_lines + checklist)


# ----------------------------------------------------------------------------- 4. Slow & Ultra-Slow Practice Generator

def _encode_varlen(val: int) -> bytes:
    low = val & 0x7F
    shifted = val >> 7
    if shifted == 0:
        return bytes([low])
    prefix = _encode_varlen(shifted)
    prefix_high = bytes(map(lambda b: b | 0x80, prefix))
    return prefix_high + bytes([low])


def write_midi_from_sequence(
    notes: list[tuple[int, Fraction]],
    tempo_bpm: int,
    out_path: Path,
    guide_click: bool = False,
    instrument: str = "piano",
) -> Path:
    """Write a Standard MIDI File (Format 1) from (midi_pitch, duration_quarters) at exact tempo_bpm."""
    tpq = 480
    us_per_beat = int(round(60_000_000 / max(1, tempo_bpm)))
    gm_zero_indexed = (INSTRUMENT_PROFILES.get(instrument.lower(), INSTRUMENT_PROFILES["piano"])[2] - 1) & 0x7F

    melody_bytes = bytearray()
    melody_bytes.extend(_encode_varlen(0) + b"\xFF\x51\x03" + struct.pack(">I", us_per_beat)[1:])
    melody_bytes.extend(_encode_varlen(0) + bytes([0xC0, gm_zero_indexed]))

    def append_note(acc: bytearray, item: tuple[int, Fraction]) -> bytearray:
        midi_pitch, dur_q = item
        ticks = max(1, int(round(float(dur_q) * tpq)))
        acc.extend(_encode_varlen(0) + bytes([0x90, midi_pitch & 0x7F, 92]))
        acc.extend(_encode_varlen(ticks) + bytes([0x80, midi_pitch & 0x7F, 0]))
        return acc

    reduce(append_note, notes, melody_bytes)
    melody_bytes.extend(_encode_varlen(0) + b"\xFF\x2F\x00")

    tracks = [bytes(melody_bytes)]
    if guide_click and notes:
        total_quarters = float(sum(map(lambda n: n[1], notes), Fraction(0)))
        n_eighths = max(1, int(round(total_quarters * 2)))
        click_ticks = tpq // 2
        click_bytes = bytearray()

        def append_click(acc: bytearray, idx: int) -> bytearray:
            drum_note = 76 if idx % 2 == 0 else 77  # Hi/Low woodblock on Channel 10 (0x99)
            vel = 68 if idx % 2 == 0 else 48
            acc.extend(_encode_varlen(0) + bytes([0x99, drum_note, vel]))
            acc.extend(_encode_varlen(click_ticks) + bytes([0x89, drum_note, 0]))
            return acc

        reduce(append_click, range(n_eighths), click_bytes)
        click_bytes.extend(_encode_varlen(0) + b"\xFF\x2F\x00")
        tracks.append(bytes(click_bytes))

    header = struct.pack(">4sIHHH", b"MThd", 6, 1, len(tracks), tpq)
    track_chunks = b"".join(map(lambda tb: struct.pack(">4sI", b"MTrk", len(tb)) + tb, tracks))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(header + track_chunks)
    return out_path


def _add_guide_click_part(root: ET.Element) -> None:
    """Add an eighth-note subdivision guide pulse part to a MusicXML score for ultra-slow practice."""
    parts = root.findall("part")
    if not parts:
        return
    part_list = root.find("part-list")
    if part_list is None:
        return
    click_id = f"P_CLICK_{len(parts) + 1}"
    sp = ET.SubElement(part_list, "score-part", id=click_id)
    ET.SubElement(sp, "part-name").text = "Practice Click (8th Subdivisions)"
    ET.SubElement(sp, "part-abbreviation").text = "Click"

    click_part = ET.SubElement(root, "part", id=click_id)
    src_measures = parts[0].findall("measure")

    def build_click_measure(state: tuple, idx_m: tuple) -> tuple:
        div, time_sig = state
        m_idx, src_m = idx_m
        m_num = src_m.attrib.get("number", str(m_idx + 1))
        attr = src_m.find("attributes")
        new_div = int(attr.findtext("divisions")) if attr is not None and attr.findtext("divisions") else div
        beats_txt = attr.findtext("./time/beats") if attr is not None else None
        btype_txt = attr.findtext("./time/beat-type") if attr is not None else None
        new_time = (int(beats_txt), int(btype_txt)) if (beats_txt and btype_txt) else time_sig

        cm = ET.SubElement(click_part, "measure", number=m_num)
        if m_idx == 0 or new_time != time_sig:
            c_attr = ET.SubElement(cm, "attributes")
            ET.SubElement(c_attr, "divisions").text = "2"
            t_el = ET.SubElement(c_attr, "time")
            ET.SubElement(t_el, "beats").text = str(new_time[0])
            ET.SubElement(t_el, "beat-type").text = str(new_time[1])
            c_el = ET.SubElement(c_attr, "clef")
            ET.SubElement(c_el, "sign").text = "G"
            ET.SubElement(c_el, "line").text = "2"

        v1_notes = list(filter(
            lambda n: (n.findtext("voice") or "1").strip() == "1" and n.find("grace") is None and n.find("chord") is None,
            src_m.findall("note"),
        ))
        bar_q = sum(map(lambda n: Fraction(int(n.findtext("duration") or "0"), new_div), v1_notes), Fraction(0))
        n_eighths = max(1, int(round(float(bar_q * 2))))

        def add_pulse(e_idx: int) -> None:
            n_el = ET.SubElement(cm, "note")
            p_el = ET.SubElement(n_el, "pitch")
            ET.SubElement(p_el, "step").text = "G" if e_idx % 2 == 0 else "C"
            ET.SubElement(p_el, "octave").text = "5"
            ET.SubElement(n_el, "duration").text = "1"
            ET.SubElement(n_el, "voice").text = "1"
            ET.SubElement(n_el, "type").text = "eighth"

        list(map(add_pulse, range(n_eighths)))
        return (new_div, new_time)

    reduce(build_click_measure, enumerate(src_measures), (1, (4, 4)))


def _filter_single_part(root: ET.Element, keep_index: int, hand_label: str) -> ET.Element:
    """Return a copy of `root` containing only part `keep_index` (for Piano RH-only or LH-only practice)."""
    cloned = copy.deepcopy(root)
    parts = cloned.findall("part")
    if keep_index >= len(parts):
        return cloned
    keep_id = parts[keep_index].attrib.get("id", "")
    part_list = cloned.find("part-list")
    if part_list is not None:
        sps = part_list.findall("score-part")
        list(map(lambda sp: part_list.remove(sp) if sp.attrib.get("id") != keep_id else None, sps))
    list(map(lambda p: cloned.remove(p) if p.attrib.get("id") != keep_id else None, parts))
    wt = cloned.find("./work/work-title")
    if wt is not None and wt.text:
        wt.text = f"{wt.text} ({hand_label})"
    return cloned


def scale_musicxml_tempo(
    src_xml_path: Path,
    out_xml_path: Path,
    speed_ratio: float | None = None,
    target_bpm: int | None = None,
    base_bpm_override: int | None = None,
    guide_click: bool = False,
    instrument: str = "auto",
) -> dict:
    """Create a tempo-scaled MusicXML file for MuseScore and verify its note parity."""
    tree = ET.parse(src_xml_path)
    root = tree.getroot()
    detected_inst = _detect_instrument(root, instrument)

    part_list = root.find("part-list")
    if part_list is not None:
        sps = part_list.findall("score-part")
        list(map(
            lambda idx_sp: _attach_midi_instrument(
                idx_sp[1],
                idx_sp[1].attrib.get("id", f"P{idx_sp[0] + 1}"),
                "violin" if (detected_inst == "violin" and idx_sp[0] == 0) else "piano",
            ),
            enumerate(sps),
        ))

    sound_els = list(filter(lambda s: "tempo" in s.attrib, root.findall(".//sound")))
    pm_els = list(filter(
        lambda pm: pm.text and pm.text.strip().replace(".", "", 1).isdigit(),
        root.findall(".//metronome/per-minute"),
    ))
    detected_bpm = (
        float(base_bpm_override) if base_bpm_override else
        float(sound_els[0].attrib["tempo"]) if sound_els else
        float(pm_els[0].text.strip()) if pm_els else
        90.0
    )
    ratio = (
        float(target_bpm) / detected_bpm if target_bpm is not None else
        float(speed_ratio) if speed_ratio is not None else
        0.5
    )
    new_bpm = max(10, int(round(detected_bpm * ratio)))
    pct = int(round(ratio * 100))

    orig_title = (
        root.findtext("./work/work-title")
        or root.findtext("./movement-title")
        or src_xml_path.stem
    )
    label = f"{pct}% Practice Speed (quarter = {new_bpm} BPM, orig. {int(round(detected_bpm))})"
    work = _ensure_child(root, "work")
    wt = _ensure_child(work, "work-title")
    wt.text = f"{orig_title} [{pct}% Speed - {new_bpm} BPM]"

    list(map(
        lambda s: s.attrib.__setitem__("tempo", str(max(10, int(round(float(s.attrib["tempo"]) * ratio))))),
        sound_els,
    ))
    list(map(
        lambda pm: setattr(pm, "text", str(max(10, int(round(float(pm.text.strip()) * ratio))))),
        pm_els,
    ))

    first_measure = root.find("./part/measure")
    if first_measure is not None and not sound_els and not pm_els:
        direction = ET.Element("direction", placement="above")
        dt = ET.SubElement(direction, "direction-type")
        words = ET.SubElement(dt, "words")
        words.text = label
        met = ET.SubElement(dt, "metronome")
        ET.SubElement(met, "beat-unit").text = "quarter"
        ET.SubElement(met, "per-minute").text = str(new_bpm)
        ET.SubElement(direction, "sound", tempo=str(new_bpm))
        first_measure.insert(0, direction)
    elif first_measure is not None:
        first_dir_dt = first_measure.find("./direction/direction-type")
        if first_dir_dt is not None:
            words_el = _ensure_child(first_dir_dt, "words")
            words_el.text = label
        if not sound_els:
            first_dir = first_measure.find("./direction")
            if first_dir is not None:
                ET.SubElement(first_dir, "sound", tempo=str(new_bpm))

    if guide_click:
        _add_guide_click_part(root)

    out_xml_path.parent.mkdir(parents=True, exist_ok=True)
    out_xml_path.write_text(serialize_score_partwise(root), encoding="utf-8")
    return {
        "speed_percent": pct,
        "original_bpm": int(round(detected_bpm)),
        "new_bpm": new_bpm,
        "instrument": detected_inst,
        "musicxml": str(out_xml_path),
        "guide_click": guide_click,
    }


def find_musescore_cli() -> str | None:
    return next(filter(lambda c: Path(c).exists() or shutil.which(c) is not None, MUSESCORE_CANDIDATES), None)


_LY_FIFTHS_MAP = {
    0: "c", 1: "g", 2: "d", 3: "a", 4: "e", 5: "b", 6: "fis", 7: "cis",
    -1: "f", -2: "bes", -3: "es", -4: "as", -5: "des", -6: "ges", -7: "ces",
}
_LY_SHARP_PC = ("c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b")
_LY_FLAT_PC = ("c", "des", "d", "ees", "e", "f", "ges", "g", "aes", "a", "bes", "b")


def _ly_pitch_from_xml(midi: int, fifths: int) -> str:
    table = _LY_FLAT_PC if fifths < 0 else _LY_SHARP_PC
    octv = (midi // 12) - 1
    marks = "'" * (octv - 3) if octv > 3 else "," * (3 - octv)
    return f"{table[midi % 12]}{marks}"


def _ly_dur_from_quarters(quarters: Fraction) -> str:
    table = {
        Fraction(8, 1): "\\breve",
        Fraction(6, 1): "1.",
        Fraction(4, 1): "1",
        Fraction(3, 1): "2.",
        Fraction(7, 2): "2..",
        Fraction(2, 1): "2",
        Fraction(3, 2): "4.",
        Fraction(7, 4): "4..",
        Fraction(1, 1): "4",
        Fraction(3, 4): "8.",
        Fraction(1, 2): "8",
        Fraction(3, 8): "16.",
        Fraction(1, 4): "16",
        Fraction(1, 8): "32",
    }
    if quarters in table:
        return table[quarters]
    if quarters.denominator == 1:
        return f"4*{quarters.numerator}"
    return f"4*{quarters.numerator}/{quarters.denominator}"


def musicxml_to_lilypond(
    xml_path: Path,
    out_ly_path: Path,
    tempo_bpm: int | None = None,
) -> Path:
    """Standalone MusicXML -> GNU LilyPond 2.26 exporter (no external dependencies)."""
    root = ET.parse(xml_path).getroot()
    title = (root.findtext("./work/work-title") or xml_path.stem).replace('"', "'").strip()
    parts = list(filter(lambda p: not p.attrib.get("id", "").startswith("P_CLICK"), root.findall("part")))
    if not parts:
        raise ValueError(f"No musical <part> found in {xml_path}")
    part = parts[0]

    sound_el = root.find(".//sound[@tempo]")
    pm_el = root.find(".//metronome/per-minute")
    bpm = tempo_bpm or (
        int(round(float(sound_el.attrib["tempo"])))
        if sound_el is not None and sound_el.attrib.get("tempo")
        else (int(round(float(pm_el.text.strip()))) if pm_el is not None and pm_el.text else 90)
    )

    def render_measure(st: tuple, idx_m: tuple) -> tuple:
        lines, cur_div, cur_fifths, cur_ts = st
        idx, m_el = idx_m
        attr = m_el.find("attributes")
        div = int(attr.findtext("divisions")) if (attr is not None and attr.findtext("divisions")) else cur_div
        fifths_txt = attr.findtext("./key/fifths") if attr is not None else None
        fifths = int(fifths_txt) if fifths_txt is not None else cur_fifths
        b_txt = attr.findtext("./time/beats") if attr is not None else None
        bt_txt = attr.findtext("./time/beat-type") if attr is not None else None
        ts = (int(b_txt), int(bt_txt)) if (b_txt and bt_txt) else cur_ts

        def group_step(g_acc: list, child: ET.Element) -> list:
            if child.tag != "note":
                return g_acc
            voice_el = child.find("voice")
            if voice_el is not None and (voice_el.text or "").strip() not in ("", "1"):
                return g_acc
            if child.find("grace") is not None:
                return g_acc
            dur_q = Fraction(int(child.findtext("duration") or str(div)), max(1, div))
            ties = set(map(lambda t: t.attrib.get("type", ""), child.findall("tie")))
            is_tie_start = "start" in ties
            if child.find("rest") is not None:
                return g_acc + [((), dur_q, False)]
            p_el = child.find("pitch")
            if p_el is None:
                return g_acc
            midi = _pitch_el_to_midi(p_el)
            if child.find("chord") is not None and g_acc and g_acc[-1][0]:
                prev_p, prev_d, prev_t = g_acc[-1]
                return g_acc[:-1] + [(tuple(sorted(set((*prev_p, midi)))), prev_d, prev_t or is_tie_start)]
            return g_acc + [((midi,), dur_q, is_tie_start)]

        grouped = reduce(group_step, list(m_el), [])
        def fmt_ev(ev: tuple) -> str:
            pitches, dur_q, tie_s = ev
            d_str = _ly_dur_from_quarters(dur_q)
            if not pitches:
                return f"r{d_str}"
            t_sym = "~" if tie_s else ""
            if len(pitches) == 1:
                return f"{_ly_pitch_from_xml(pitches[0], fifths)}{d_str}{t_sym}"
            body = " ".join(map(lambda m: _ly_pitch_from_xml(m, fifths), pitches))
            return f"<{body}>{d_str}{t_sym}"

        prefix = (
            f"\\key {_LY_FIFTHS_MAP.get(fifths, 'c')} \\major \\time {ts[0]}/{ts[1]} \\tempo 4 = {bpm} "
            if idx == 0 else (f"\\time {ts[0]}/{ts[1]} " if ts != cur_ts else "")
        )
        m_line = "    " + prefix + " ".join(map(fmt_ev, grouped)) + " |"
        return lines + [m_line], div, fifths, ts

    bar_lines, _, _, _ = reduce(render_measure, enumerate(part.findall("measure")), ([], 4, 0, (4, 4)))
    ly_text = (
        '\\version "2.26.0"\n'
        "\\header {\n"
        f'  title = "{title}"\n'
        "  tagline = ##f\n"
        "}\n"
        "\\score {\n"
        "  \\new Staff {\n"
        '    \\clef "treble"\n'
        + "\n".join(bar_lines)
        + '\n    \\bar "|."\n'
        "  }\n"
        "  \\layout { }\n"
        "  \\midi { }\n"
        "}\n"
    )
    out_ly_path.parent.mkdir(parents=True, exist_ok=True)
    out_ly_path.write_text(ly_text, encoding="utf-8")
    return out_ly_path


def try_lean_verify(
    ref_xml_path: Path,
    extra_xmls: tuple[tuple[str, Path, float], ...] = (),
    extra_lys: tuple[tuple[str, Path, float], ...] = (),
    extra_mids: tuple[tuple[str, Path, float], ...] = (),
) -> dict:
    """Run Lean 4 `score_verifier` if inside the SheetMusicReader repo; otherwise skip cleanly."""
    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from sheet_music_reader.export import lean_bridge
        if not lean_bridge.SCORE_VERIFIER_BIN.is_file():
            return {"lean_available": False, "skipped": True, "reason": "score_verifier binary not built"}
    except Exception as exc:
        return {"lean_available": False, "skipped": True, "reason": str(exc)}

    ref_spec = lean_bridge.spec_from_musicxml_file(ref_xml_path)
    def mk_ratio(sp: float) -> tuple[int, int]:
        fr = Fraction(max(0.05, float(sp))).limit_denominator(1000)
        return int(fr.numerator), int(fr.denominator)

    score_entries = (
        *map(lambda item: (item[0], lean_bridge.spec_from_musicxml_file(item[1]), 1, *mk_ratio(item[2])), extra_xmls),
        *map(lambda item: (item[0], lean_bridge.spec_from_lilypond_file(item[1]), 1, *mk_ratio(item[2])), extra_lys),
    )
    def mid_entry(item: tuple) -> tuple:
        name, p, sp = item
        notes, tn, td = lean_bridge.sounding_notes_from_midi_file(p)
        sn, sd = mk_ratio(sp)
        return (name, notes, 1, sn, sd, tn, td)

    note_entries = tuple(map(mid_entry, extra_mids))
    rep = lean_bridge.verify_bundle_with_lean(
        reference=("source_musicxml", ref_spec),
        score_entries=score_entries,
        note_entries=note_entries,
    )
    return {"lean_available": True, "skipped": False, **rep}


def generate_slow_practice_pack(
    src_xml_path: Path,
    out_dir: Path,
    speeds: tuple[float, ...] = (1.0, 0.75, 0.5, 0.33, 0.25),
    bpms: tuple[int, ...] = (),
    base_bpm: int | None = None,
    guide_click_below: float = 0.40,
    force_guide_click: bool = False,
    instrument: str = "auto",
    hands_separate: bool = False,
    export_mscz: bool = False,
    emit_lilypond: bool = False,
    lean_verify: bool = False,
) -> dict:
    """Generate a full Slow Practice Pack (.musicxml + .mid) and double-check every output file."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", src_xml_path.stem)
    orig_seq = extract_sounding_sequence(src_xml_path, part_index=0)
    mscore_bin = find_musescore_cli() if export_mscz else None

    tasks = (
        list(map(lambda b: ("bpm", b), bpms))
        if bpms else
        list(map(lambda s: ("ratio", s), speeds))
    )

    def build_one(task: tuple) -> dict:
        kind, val = task
        use_click = force_guide_click or (kind == "ratio" and val <= guide_click_below and val < 1.0)
        tag = f"{int(round(val))}bpm" if kind == "bpm" else f"{int(round(val * 100))}pct"
        xml_out = out_dir / f"{stem}_{tag}.musicxml"
        info = scale_musicxml_tempo(
            src_xml_path,
            xml_out,
            speed_ratio=val if kind == "ratio" else None,
            target_bpm=int(val) if kind == "bpm" else None,
            base_bpm_override=base_bpm,
            guide_click=use_click,
            instrument=instrument,
        )
        mid_out = out_dir / f"{stem}_{tag}_{info['new_bpm']}bpm.mid"
        write_midi_from_sequence(orig_seq, info["new_bpm"], mid_out, guide_click=use_click, instrument=info["instrument"])
        new_seq = extract_sounding_sequence(xml_out, part_index=0)
        parity_ok = new_seq == orig_seq

        hand_files = {}
        if hands_separate:
            scaled_root = ET.parse(xml_out).getroot()
            non_click_parts = list(filter(lambda p: not p.attrib.get("id", "").startswith("P_CLICK"), scaled_root.findall("part")))
            if len(non_click_parts) >= 2:
                rh_xml = out_dir / f"{stem}_{tag}_RH_only.musicxml"
                lh_xml = out_dir / f"{stem}_{tag}_LH_only.musicxml"
                rh_xml.write_text(serialize_score_partwise(_filter_single_part(scaled_root, 0, "Right Hand Only")), encoding="utf-8")
                lh_xml.write_text(serialize_score_partwise(_filter_single_part(scaled_root, 1, "Left Hand Only")), encoding="utf-8")
                hand_files = {"right_hand_musicxml": str(rh_xml), "left_hand_musicxml": str(lh_xml)}

        mscz_out = None
        if mscore_bin:
            mscz_path = out_dir / f"{stem}_{tag}.mscz"
            subprocess.run([mscore_bin, "-o", str(mscz_path), str(xml_out)], capture_output=True, text=True)
            mscz_out = str(mscz_path) if mscz_path.exists() else None
        ly_out_path = None
        if emit_lilypond:
            ly_out = out_dir / f"{stem}_{tag}.ly"
            musicxml_to_lilypond(xml_out, ly_out, tempo_bpm=info["new_bpm"])
            ly_out_path = str(ly_out)
        ratio = (Fraction(info["new_bpm"], max(1, info["original_bpm"])) if kind == "bpm" else val)
        return {
            **info,
            "midi": str(mid_out),
            "lilypond": ly_out_path,
            "mscz": mscz_out,
            "hands_separate": hand_files,
            "note_parity_verified": parity_ok,
            "_ratio": float(ratio),
        }

    generated = list(map(build_one, tasks))
    audit = verify_musicxml(src_xml_path, instrument=instrument)
    lean_res = None
    if lean_verify:
        xml_items = tuple(map(lambda g: (f"xml_{g['speed_percent']}", Path(g["musicxml"]), g["_ratio"]), generated))
        ly_items = tuple(map(lambda g: (f"ly_{g['speed_percent']}", Path(g["lilypond"]), g["_ratio"]), filter(lambda g: g.get("lilypond"), generated)))
        mid_items = tuple(map(lambda g: (f"mid_{g['speed_percent']}", Path(g["midi"]), g["_ratio"]), generated))
        lean_res = try_lean_verify(src_xml_path, xml_items, ly_items, mid_items)
    clean_generated = list(map(lambda g: dict(filter(lambda kv: kv[0] != "_ratio", g.items())), generated))
    return {
        "source": str(src_xml_path),
        "instrument": audit["instrument"],
        "source_audit_status": audit["status"],
        "source_suspect_bars": len(audit["suspect_bars"]),
        "practice_files": clean_generated,
        "all_parity_verified": all(map(lambda g: g["note_parity_verified"], generated)),
        "lean_verification": lean_res,
    }


# ----------------------------------------------------------------------------- 5. Repo Bridge (`from-repo`)

def convert_with_repo_tools(
    input_path: Path,
    out_dir: Path,
    title: str | None = None,
    instrument: str = "auto",
    emit_lilypond: bool = False,
) -> dict:
    """Convert a PDF or image using vector_omr.py or score_from_image.py into MusicXML + MIDI."""
    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    info = inspect_file(input_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", input_path.stem)
    xml_path = out_dir / f"{stem}.musicxml"
    mid_path = out_dir / f"{stem}.mid"

    if info["kind"] == "vector_pdf":
        from sheet_music_reader.omr import vector_omr as vomr
        score = vomr.read_score(input_path)
        xml_text = vector_score_to_musicxml(score, title=title, instrument=instrument)
        xml_path.write_text(xml_text, encoding="utf-8")
        vomr.write_midi(score, mid_path, as_written=True)
    elif info["kind"] in ("image_score", "scanned_pdf"):
        from sheet_music_reader.omr import score_from_image as sfi
        rep = sfi.convert(input_path, out_dir, use_audiveris=False, title=title)
        raw_xml = Path(rep["outputs"]["homr_musicxml"])
        parsed = sfi.tidy(sfi.restore_silent_rests(sfi.from_musicxml(raw_xml)))
        xml_path.write_text(image_score_to_musicxml(parsed, instrument=instrument), encoding="utf-8")
        shutil.copy(rep["outputs"]["midi"], mid_path)
    elif info["kind"] == "musicxml":
        shutil.copy(input_path, xml_path)
        seq = extract_sounding_sequence(xml_path)
        write_midi_from_sequence(seq, 90, mid_path, instrument=instrument if instrument != "auto" else "piano")
    else:
        raise ValueError(f"Unsupported input kind: {info['kind']}")

    ly_path = out_dir / f"{stem}.ly" if emit_lilypond else None
    if ly_path is not None:
        musicxml_to_lilypond(xml_path, ly_path)

    audit = verify_musicxml(xml_path, instrument=instrument)
    return {
        "input": str(input_path),
        "kind": info["kind"],
        "musicxml": str(xml_path),
        "midi": str(mid_path),
        "lilypond": str(ly_path) if ly_path else None,
        "audit": audit,
    }


# ----------------------------------------------------------------------------- 6. CLI Entrypoint

def _parse_float_list(raw: str) -> tuple[float, ...]:
    parts = filter(None, map(str.strip, raw.split(",")))
    return tuple(map(lambda s: float(s.rstrip("%")) / 100.0 if s.endswith("%") or float(s.rstrip("%")) > 3.0 else float(s), parts))


def _parse_int_list(raw: str) -> tuple[int, ...]:
    return tuple(map(int, filter(None, map(str.strip, raw.split(","))))) if raw else ()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ins = sub.add_parser("inspect", help="Check whether a PDF is digital vector music or a scan/photo")
    p_ins.add_argument("path", type=Path)

    p_repo = sub.add_parser("from-repo", help="Convert a PDF/image to MusicXML using repo OMR tools")
    p_repo.add_argument("path", type=Path)
    p_repo.add_argument("--out", type=Path, default=Path("data/output/digitized_scores/musescore_out"))
    p_repo.add_argument("--title", default=None)
    p_repo.add_argument("--instrument", choices=("auto", "violin", "piano"), default="auto")
    p_repo.add_argument("--lilypond", action="store_true", help="Also emit a GNU LilyPond (.ly) file")

    p_ver = sub.add_parser("verify", help="Run the automated Double-Check Audit on a MusicXML file")
    p_ver.add_argument("musicxml", type=Path)
    p_ver.add_argument("--instrument", choices=("auto", "violin", "piano"), default="auto")
    p_ver.add_argument("--reference", type=Path, default=None, help="Optional trusted MIDI or MusicXML to compare against")
    p_ver.add_argument("--json", type=Path, default=None, help="Write full audit JSON report to this path")
    p_ver.add_argument("--lean-verify", action="store_true", help="Also run Lean 4 kernel bar/pitch check when available")

    p_slow = sub.add_parser("slow", help="Generate slow and ultra-slow practice MusicXML + MIDI files for MuseScore")
    p_slow.add_argument("musicxml", type=Path)
    p_slow.add_argument("--out", type=Path, default=None, help="Output folder (defaults to <file>_practice_pack)")
    p_slow.add_argument(
        "--speeds",
        default="1.0,0.75,0.5,0.33,0.25",
        help="Comma-separated speed ratios or percentages (e.g. '0.5,0.33,0.25' or '75%,50%,33%,25%')",
    )
    p_slow.add_argument("--bpm", default="", help="Optional comma-separated exact BPM targets (e.g. '60,45,30')")
    p_slow.add_argument("--base-bpm", type=int, default=None, help="Override original BPM if score has no tempo mark")
    p_slow.add_argument("--instrument", choices=("auto", "violin", "piano"), default="auto")
    p_slow.add_argument("--hands-separate", action="store_true", help="For piano scores, also save Right-Hand-only and Left-Hand-only files")
    p_slow.add_argument("--guide-click", action="store_true", help="Add an 8th-note subdivision guide pulse part")
    p_slow.add_argument("--no-auto-click", action="store_true", help="Disable automatic guide click on <=40%% speeds")
    p_slow.add_argument("--export-mscz", action="store_true", help="Also save native .mscz files if MuseScore is installed")
    p_slow.add_argument("--lilypond", action="store_true", help="Also generate GNU LilyPond (.ly) files for each speed")
    p_slow.add_argument("--lean-verify", action="store_true", help="Verify all generated formats with Lean 4 when available")

    args = ap.parse_args(argv[1:])

    if args.cmd == "inspect":
        res = inspect_file(args.path)
        print(json.dumps(res, indent=2))
        return 0 if "error" not in res else 1

    if args.cmd == "from-repo":
        res = convert_with_repo_tools(args.path, args.out, title=args.title, instrument=args.instrument, emit_lilypond=args.lilypond)
        print(format_verification_report(res["audit"]))
        print(f"\nSaved MuseScore MusicXML : {res['musicxml']}")
        print(f"Saved Standard MIDI      : {res['midi']}")
        if res.get("lilypond"):
            print(f"Saved GNU LilyPond (.ly) : {res['lilypond']}")
        return 0 if res["audit"]["passed"] else 1

    if args.cmd == "verify":
        rep = verify_musicxml(args.musicxml, reference_path=args.reference, instrument=args.instrument)
        print(format_verification_report(rep))
        lean_ok = True
        if args.lean_verify:
            mids = (("ref_midi", args.reference, 1.0),) if args.reference and args.reference.suffix.lower() in (".mid", ".midi") else ()
            xmls = (("ref_xml", args.reference, 1.0),) if args.reference and args.reference.suffix.lower() in (".xml", ".musicxml") else ()
            lys = (("ref_ly", args.reference, 1.0),) if args.reference and args.reference.suffix.lower() == ".ly" else ()
            lrep = try_lean_verify(args.musicxml, extra_xmls=xmls, extra_lys=lys, extra_mids=mids)
            rep["lean_verification"] = lrep
            print(f"Lean 4 Check : {'PASS' if lrep.get('ok') else ('SKIPPED (' + lrep.get('reason', '') + ')' if lrep.get('skipped') else 'FAIL')}")
            if not lrep.get("skipped") and not lrep.get("ok"):
                lean_ok = False
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        return 0 if (rep["passed"] and lean_ok) else 1

    if args.cmd == "slow":
        out_dir = args.out or (args.musicxml.parent / f"{args.musicxml.stem}_practice_pack")
        speeds = _parse_float_list(args.speeds)
        bpms = _parse_int_list(args.bpm)
        pack = generate_slow_practice_pack(
            args.musicxml,
            out_dir,
            speeds=speeds,
            bpms=bpms,
            base_bpm=args.base_bpm,
            guide_click_below=0.0 if args.no_auto_click else 0.40,
            force_guide_click=args.guide_click,
            instrument=args.instrument,
            hands_separate=args.hands_separate,
            export_mscz=args.export_mscz,
            emit_lilypond=args.lilypond,
            lean_verify=args.lean_verify,
        )
        print(f"=== Slow Practice Pack Generated ({len(pack['practice_files'])} speeds, {pack['instrument'].capitalize()}) ===")
        print(f"Source Score Audit : {pack['source_audit_status']} ({pack['source_suspect_bars']} suspect bars)")
        print(f"Note Parity Check  : {'PASS (100% identical notes across all speeds)' if pack['all_parity_verified'] else 'FAIL'}")
        if pack.get("lean_verification") is not None:
            lv = pack["lean_verification"]
            print(f"Lean 4 Verification: {'PASS' if lv.get('ok') else ('SKIPPED' if lv.get('skipped') else 'FAIL')}")
        lines = list(map(
            lambda pf: (
                f"  - {pf['speed_percent']:3d}% speed ({pf['new_bpm']:3d} BPM, orig {pf['original_bpm']} BPM)"
                f"{' [+8th guide click]' if pf['guide_click'] else ''}\n"
                f"      MusicXML : {pf['musicxml']}\n"
                f"      MIDI     : {pf['midi']}"
                + (f"\n      LilyPond : {pf['lilypond']}" if pf.get("lilypond") else "")
                + (
                    f"\n      Piano RH : {pf['hands_separate']['right_hand_musicxml']}\n"
                    f"      Piano LH : {pf['hands_separate']['left_hand_musicxml']}"
                    if pf.get("hands_separate") else ""
                )
            ),
            pack["practice_files"],
        ))
        print("\n".join(lines))
        lean_ok = True if (pack.get("lean_verification") is None or pack["lean_verification"].get("skipped")) else bool(pack["lean_verification"].get("ok"))
        return 0 if (pack["all_parity_verified"] and lean_ok) else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

# <!-- APAF Bioinformatics | musescore_helper.py | Approved | 2026-11-15 -->
