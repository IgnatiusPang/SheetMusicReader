"""Bridge between SheetMusicReader formats and the Lean 4 `score_verifier` kernel binary.

Provides independent disk parsers (Gate D5 anti-self-comparison) for:
- vector_omr.Score
- Psalms JSON dictionaries
- MusicXML 3.1 (.musicxml / .xml) on disk
- GNU LilyPond (.ly) on disk
- Standard MIDI (.mid) on disk via mido

Also invokes `formalization/lean/.lake/build/bin/score_verifier` and optionally
generates standalone `<stem>_cert.lean` files checked directly by `lake env lean`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from fractions import Fraction
from functools import reduce
from itertools import chain, groupby
from pathlib import Path
from typing import Any, Sequence

import mido

TICKS_PER_QUARTER = 48
TICKS_PER_WHOLE = 192

PROJECT_ROOT = Path(__file__).resolve().parent
LEAN_DIR = PROJECT_ROOT / "formalization" / "lean"
SCORE_VERIFIER_BIN = LEAN_DIR / ".lake" / "build" / "bin" / "score_verifier"

_STEP_TO_SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_LY_LETTER_TO_SEMITONE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
_TIME_NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4}

_NOTE_TO_SEMI_RE = re.compile(r"^([A-Ga-g])([#♯b♭]*)(-?\d+)$")
_LY_NOTE_RE = re.compile(
    r"^([a-g])((?:is|es|s|f)*)([,']*)(?:(\\breve|\d+)(?:(\.\.|\.)?)?(?:\*(\d+)(?:/(\d+))?)?)?(~)?$"
)
_LY_REST_RE = re.compile(
    r"^[rRsS](?:(\\breve|\d+)(?:(\.\.|\.)?)?(?:\*(\d+)(?:/(\d+))?)?)?$"
)
_LY_CHORD_RE = re.compile(
    r"^<([^>]+)>(?:(\\breve|\d+)(?:(\.\.|\.)?)?(?:\*(\d+)(?:/(\d+))?)?)?(~)?$"
)


@dataclass(frozen=True)
class LeanEvent:
    kind: str  # "N" or "R"
    ticks: int
    tie_start: bool = False
    tie_stop: bool = False
    pitches: tuple[int, ...] = ()


@dataclass(frozen=True)
class LeanBar:
    bar_number: int
    beats: int
    beat_type: int
    expected_ticks: int
    events: tuple[LeanEvent, ...]


@dataclass(frozen=True)
class LeanScoreSpec:
    title: str
    tempo_num: int
    tempo_den: int
    bars: tuple[LeanBar, ...]


@dataclass(frozen=True)
class LeanSoundingNote:
    ticks: int
    pitches: tuple[int, ...]


def quarters_to_ticks(quarter_beats: float | Fraction) -> int:
    """Convert quarter-note duration to exact 48-tick units."""
    frac = quarter_beats if isinstance(quarter_beats, Fraction) else Fraction(float(quarter_beats)).limit_denominator(48)
    ticks = int(round(float(frac * TICKS_PER_QUARTER)))
    return max(0, ticks)


def float_to_ratio(val: float, max_den: int = 1000) -> tuple[int, int]:
    """Convert positive float to positive reduced integer ratio `(num, den)`."""
    frac = Fraction(max(1e-4, float(val))).limit_denominator(max_den)
    return max(1, int(frac.numerator)), max(1, int(frac.denominator))


def expected_bar_ticks(beats: int, beat_type: int) -> int:
    """Return exact expected ticks per measure for `beats / beat_type`."""
    return (max(1, int(beats)) * TICKS_PER_WHOLE) // max(1, int(beat_type))


def note_name_to_midi(name: str, default_midi: int = 60) -> int:
    """Parse pitch names like `C4`, `F#4`, `Bb3` to MIDI integer."""
    if not name or str(name).upper() == "REST":
        return default_midi
    cleaned = str(name).strip().replace("♯", "#").replace("♭", "b")
    m = _NOTE_TO_SEMI_RE.match(cleaned)
    if not m:
        return default_midi
    letter, accs, octv = m.group(1).upper(), m.group(2), int(m.group(3))
    alter = accs.count("#") - accs.count("b")
    return 12 * (octv + 1) + _STEP_TO_SEMITONE.get(letter, 0) + alter


def _mark_adjacent_ties(events: Sequence[LeanEvent]) -> tuple[LeanEvent, ...]:
    """Ensure `tie_stop` is consistent whenever the previous event ties forward with matching pitches."""
    def step(acc: tuple[list[LeanEvent], LeanEvent | None], ev: LeanEvent) -> tuple[list[LeanEvent], LeanEvent | None]:
        out, prev = acc
        stop = bool(
            ev.tie_stop
            or (
                prev is not None
                and prev.kind == "N"
                and ev.kind == "N"
                and prev.tie_start
                and prev.pitches == ev.pitches
            )
        )
        updated = LeanEvent(ev.kind, ev.ticks, ev.tie_start, stop, ev.pitches)
        return [*out, updated], updated

    res, _ = reduce(step, events, ([], None))
    return tuple(res)


# ------------------------------------------------------------------ converters


def spec_from_vector_score(score: Any, lane: int = 0, arrangement: bool = False) -> LeanScoreSpec:
    """Build a LeanScoreSpec directly from an in-memory `vector_omr.Score` lane."""
    raw_measures = tuple(
        chain.from_iterable(
            map(
                lambda sys: sys[lane].measures if lane < len(sys) else (),
                getattr(score, "systems", ()),
            )
        )
    )
    t_num, t_den = float_to_ratio(getattr(score, "tempo", 100.0))

    def conv_event(ev: Any) -> LeanEvent:
        ticks = quarters_to_ticks(getattr(ev, "value", 1.0))
        midis = tuple(sorted(set(map(int, getattr(ev, "midis", ())))))
        if midis and ticks > 0:
            return LeanEvent("N", ticks, bool(getattr(ev, "tie", False)), False, midis)
        return LeanEvent("R", max(1, ticks), False, False, ())

    def _measure_events_for_mode(m: Any, activate_extra: bool) -> tuple[LeanEvent, ...]:
        all_ev = tuple(getattr(m, "events", ()))
        reg_raw = tuple(filter(lambda ev: not getattr(ev, "extra", False), all_ev))
        ext_raw = tuple(filter(lambda ev: bool(getattr(ev, "extra", False)), all_ev))
        reg_lean = tuple(map(conv_event, reg_raw))
        if activate_extra and ext_raw and reg_lean:
            ext_lean = tuple(map(conv_event, ext_raw))
            ext_ticks = sum(map(lambda e: e.ticks, ext_lean))
            if reg_lean[-1].kind == "R" and reg_lean[-1].ticks >= ext_ticks:
                rem = reg_lean[-1].ticks - ext_ticks
                prefix = (*reg_lean[:-1], LeanEvent("R", rem, False, False, ())) if rem > 0 else reg_lean[:-1]
                return (*prefix, *ext_lean)
        return reg_lean

    if arrangement and lane == 0:
        import vector_omr

        arr = tuple(vector_omr.arrangement(score))

        def next_verse_needs_pickup(next_sec: Any) -> bool:
            if next_sec is None or getattr(next_sec, "kind", "") != "verse":
                return False
            nsi, nv, _ = next_sec.parts[0]
            nms = (
                score.systems[nsi][nv].measures
                if (nsi < len(score.systems) and nv < len(score.systems[nsi]))
                else ()
            )
            if not nms:
                return False
            fev = next(filter(lambda ev: not getattr(ev, "extra", False), getattr(nms[0], "events", ())), None)
            return bool(fev is not None and getattr(fev, "midis", ()))

        def tag_section(idx_sf: tuple[int, Any]) -> tuple[tuple[Any, bool, bool], ...]:
            sec_idx, (sec, silence_flag) = idx_sf
            next_sec = arr[sec_idx + 1][0] if sec_idx + 1 < len(arr) else None
            activate_last = bool(
                not silence_flag
                and getattr(sec, "kind", "") == "response"
                and next_verse_needs_pickup(next_sec)
            )
            sec_ms = tuple(
                chain.from_iterable(
                    map(
                        lambda p: score.systems[p[0]][p[1]].measures
                        if (p[0] < len(score.systems) and p[1] < len(score.systems[p[0]]))
                        else (),
                        sec.parts,
                    )
                )
            )
            last_i = len(sec_ms) - 1
            return tuple(
                map(
                    lambda im: (im[1], (im[0] == last_i) and activate_last, im[0] == last_i),
                    enumerate(sec_ms),
                )
            )

        tagged_measures = tuple(chain.from_iterable(map(tag_section, enumerate(arr))))
    else:
        last_i = len(raw_measures) - 1
        tagged_measures = tuple(map(lambda im: (im[1], False, im[0] == last_i), enumerate(raw_measures)))

    def conv_bar(
        idx_tag: tuple[int, tuple[Any, bool, bool]],
        open_tie_pitches: tuple[int, ...] | None,
    ) -> tuple[LeanBar, tuple[int, ...] | None]:
        idx, (m, activate_extra, is_sec_end) = idx_tag
        ts = getattr(m, "time", (4, 4))
        beats = max(1, int(ts[0]))
        beat_type = max(1, int(ts[1]))
        exp_t = expected_bar_ticks(beats, beat_type)
        raw_evs = _measure_events_for_mode(m, activate_extra)
        if open_tie_pitches is not None and raw_evs and raw_evs[0].kind == "N" and raw_evs[0].pitches == open_tie_pitches:
            first = LeanEvent("N", raw_evs[0].ticks, raw_evs[0].tie_start, True, raw_evs[0].pitches)
            raw_evs = (first, *raw_evs[1:])
        if is_sec_end and raw_evs and raw_evs[-1].tie_start:
            last_ev = raw_evs[-1]
            raw_evs = (*raw_evs[:-1], LeanEvent(last_ev.kind, last_ev.ticks, False, last_ev.tie_stop, last_ev.pitches))
        evs = _mark_adjacent_ties(raw_evs)
        next_tie = None if is_sec_end else (evs[-1].pitches if (evs and evs[-1].kind == "N" and evs[-1].tie_start) else None)
        bar = LeanBar(idx + 1, beats, beat_type, exp_t, evs)
        return bar, next_tie

    def fold_bars(
        acc: tuple[list[LeanBar], tuple[int, ...] | None],
        idx_tag: tuple[int, tuple[Any, bool, bool]],
    ) -> tuple[list[LeanBar], tuple[int, ...] | None]:
        bars_out, open_t = acc
        bar, next_t = conv_bar(idx_tag, open_t)
        return [*bars_out, bar], next_t

    bars_list, _ = reduce(fold_bars, enumerate(tagged_measures), ([], None))
    title = Path(getattr(score, "path", "VectorScore")).stem
    return LeanScoreSpec(title=title, tempo_num=t_num, tempo_den=t_den, bars=tuple(bars_list))


def _events_to_bars(
    events: Sequence[LeanEvent],
    beats: int,
    beat_type: int,
    pad_final_bar: bool = True,
) -> tuple[LeanBar, ...]:
    """Chunk flat event list strictly at bar capacity boundaries without splitting events unless exact."""
    cap = expected_bar_ticks(beats, beat_type)

    def step(
        acc: tuple[list[LeanBar], list[LeanEvent], int, int],
        ev: LeanEvent,
    ) -> tuple[list[LeanBar], list[LeanEvent], int, int]:
        done, cur, cur_t, bar_idx = acc
        next_t = cur_t + ev.ticks
        new_cur = [*cur, ev]
        if next_t == cap:
            bar = LeanBar(bar_idx, beats, beat_type, cap, tuple(new_cur))
            return [*done, bar], [], 0, bar_idx + 1
        if next_t > cap and cur_t > 0:
            # Split note/rest across barline if an event spans across measure capacity
            head_t = cap - cur_t
            tail_t = ev.ticks - head_t
            head_ev = LeanEvent(ev.kind, head_t, ev.kind == "N", ev.tie_stop, ev.pitches)
            tail_ev = LeanEvent(ev.kind, tail_t, ev.tie_start, ev.kind == "N", ev.pitches)
            bar = LeanBar(bar_idx, beats, beat_type, cap, (*cur, head_ev))
            return step(([*done, bar], [], 0, bar_idx + 1), tail_ev)
        return done, new_cur, next_t, bar_idx

    done, cur, cur_t, bar_idx = reduce(step, events, ([], [], 0, 1))
    if cur:
        final_evs = tuple(cur)
        if pad_final_bar and cur_t < cap:
            final_evs = (*final_evs, LeanEvent("R", cap - cur_t, False, False, ()))
        done = [*done, LeanBar(bar_idx, beats, beat_type, cap, final_evs)]
    return tuple(done)


_DURATION_NAME_TO_BEATS = {
    "breve": 8.0,
    "whole": 4.0,
    "dotted_half": 3.0,
    "half": 2.0,
    "dotted_quarter": 1.5,
    "quarter": 1.0,
    "dotted_eighth": 0.75,
    "eighth": 0.5,
    "16th": 0.25,
    "sixteenth": 0.25,
    "32nd": 0.125,
}


def _note_beats_from_dict(n: dict[str, Any]) -> float:
    raw_beats = n.get("beats")
    if raw_beats is not None:
        return float(raw_beats)
    raw_dur = n.get("duration", 1.0)
    if isinstance(raw_dur, (int, float)):
        return float(raw_dur)
    return _DURATION_NAME_TO_BEATS.get(str(raw_dur).strip().lower(), 1.0)


def spec_from_psalm_data(
    psalm_data: dict[str, Any],
    speed: float = 1.0,
    augment: int = 1,
    pad_incomplete_bars: bool = True,
) -> LeanScoreSpec:
    """Build a LeanScoreSpec from a `psalms_db` score dictionary."""
    title = str(psalm_data.get("id") or psalm_data.get("title") or "Psalm")
    base_tempo = float(psalm_data.get("tempo", 90.0))
    eff_tempo = max(5.0, base_tempo * max(0.05, float(speed)))
    t_num, t_den = float_to_ratio(eff_tempo)

    ts_parts = str(psalm_data.get("time_signature", "4/4")).split("/")
    beats = max(1, int(ts_parts[0])) if ts_parts else 4
    beat_type = max(1, int(ts_parts[1])) if len(ts_parts) > 1 else 4
    aug_k = max(1, int(augment))
    scaled_beats = beats * aug_k

    raw_notes = psalm_data.get("response", {}).get("notes", [])

    def conv_note(n: dict[str, Any]) -> LeanEvent:
        dur_q = _note_beats_from_dict(n) * aug_k
        ticks = max(1, quarters_to_ticks(dur_q))
        is_rest = bool(n.get("rest")) or bool(n.get("is_rest")) or str(n.get("pitch", "")).upper() == "REST" or (n.get("midi") is None and not n.get("chord_midis"))
        if is_rest:
            return LeanEvent("R", ticks, False, False, ())
        pitches = n.get("chord_midis")
        if pitches:
            pitch_tuple = tuple(sorted(set(map(int, pitches))))
        elif "midi" in n and n["midi"] is not None:
            pitch_tuple = (int(n["midi"]),)
        else:
            pitch_tuple = (note_name_to_midi(str(n.get("pitch", "C4"))),)
        tie_val = str(n.get("tie") or "").lower()
        return LeanEvent(
            "N",
            ticks,
            tie_start=(tie_val in ("start", "both", "continue", "true", "1") or n.get("tie") is True),
            tie_stop=(tie_val in ("stop", "both", "continue")),
            pitches=pitch_tuple,
        )

    events = _mark_adjacent_ties(tuple(map(conv_note, raw_notes)))
    bars = _events_to_bars(events, scaled_beats, beat_type, pad_final_bar=pad_incomplete_bars)
    return LeanScoreSpec(title=title, tempo_num=t_num, tempo_den=t_den, bars=bars)


# ------------------------------------------------------------ independent disk parsers (D5)


def spec_from_musicxml_file(xml_path: Path, part_index: int = 0) -> LeanScoreSpec:
    """Independently parse a written MusicXML 3.1 file on disk into a LeanScoreSpec."""
    xml_path = Path(xml_path)
    root = ET.parse(xml_path).getroot()
    work_title_el = root.find("./work/work-title")
    title = (work_title_el.text or xml_path.stem).strip() if work_title_el is not None else xml_path.stem

    parts = root.findall("./part")
    if not parts:
        return LeanScoreSpec(title=title, tempo_num=100, tempo_den=1, bars=())
    part = parts[min(part_index, len(parts) - 1)]

    # Extract initial tempo from <sound tempo="..."> or <metronome>/<per-minute>
    sound_el = part.find(".//sound[@tempo]")
    per_min_el = part.find(".//metronome/per-minute")
    if sound_el is not None and sound_el.attrib.get("tempo"):
        bpm = float(sound_el.attrib["tempo"])
    elif per_min_el is not None and (per_min_el.text or "").strip():
        bpm = float(per_min_el.text.strip())
    else:
        bpm = 100.0
    t_num, t_den = float_to_ratio(bpm)

    def parse_measure(
        acc: tuple[list[LeanBar], int, int, int],
        idx_m: tuple[int, ET.Element],
    ) -> tuple[list[LeanBar], int, int, int]:
        bars_out, cur_div, cur_beats, cur_beat_type = acc
        idx, m_el = idx_m
        div_el = m_el.find("./attributes/divisions")
        if div_el is not None and (div_el.text or "").strip():
            cur_div = max(1, int(float(div_el.text.strip())))
        beats_el = m_el.find("./attributes/time/beats")
        btype_el = m_el.find("./attributes/time/beat-type")
        if beats_el is not None and (beats_el.text or "").strip():
            cur_beats = max(1, int(beats_el.text.strip()))
        if btype_el is not None and (btype_el.text or "").strip():
            cur_beat_type = max(1, int(btype_el.text.strip()))

        m_num_attr = m_el.attrib.get("number", str(idx + 1))
        bar_num = int(m_num_attr) if str(m_num_attr).isdigit() else idx + 1

        def step_note(ev_list: list[LeanEvent], child: ET.Element) -> list[LeanEvent]:
            if child.tag != "note":
                return ev_list
            # Only parse voice 1 (or unannotated voice) for canonical single-lane comparison
            voice_el = child.find("./voice")
            if voice_el is not None and (voice_el.text or "").strip() not in ("", "1"):
                return ev_list
            dur_el = child.find("./duration")
            raw_dur = int(float(dur_el.text.strip())) if (dur_el is not None and dur_el.text) else cur_div
            ticks = int(round(float(Fraction(raw_dur * TICKS_PER_QUARTER, cur_div))))
            is_rest = child.find("./rest") is not None
            is_chord = child.find("./chord") is not None
            tie_types = set(map(lambda t: t.attrib.get("type", ""), child.findall("./tie")))
            tie_start = "start" in tie_types
            tie_stop = "stop" in tie_types

            if is_rest:
                return [*ev_list, LeanEvent("R", ticks, False, False, ())]

            pitch_el = child.find("./pitch")
            if pitch_el is None:
                return ev_list
            step_txt = (pitch_el.findtext("./step") or "C").strip().upper()
            alter_txt = (pitch_el.findtext("./alter") or "0").strip()
            octv_txt = (pitch_el.findtext("./octave") or "4").strip()
            midi = 12 * (int(octv_txt) + 1) + _STEP_TO_SEMITONE.get(step_txt, 0) + int(round(float(alter_txt)))

            if is_chord and ev_list and ev_list[-1].kind == "N":
                prev = ev_list[-1]
                merged_pitches = tuple(sorted(set((*prev.pitches, midi))))
                merged = LeanEvent(
                    "N",
                    prev.ticks,
                    prev.tie_start or tie_start,
                    prev.tie_stop or tie_stop,
                    merged_pitches,
                )
                return [*ev_list[:-1], merged]
            return [*ev_list, LeanEvent("N", ticks, tie_start, tie_stop, (midi,))]

        evs = tuple(reduce(step_note, list(m_el), []))
        bar = LeanBar(
            bar_number=bar_num,
            beats=cur_beats,
            beat_type=cur_beat_type,
            expected_ticks=expected_bar_ticks(cur_beats, cur_beat_type),
            events=evs,
        )
        return [*bars_out, bar], cur_div, cur_beats, cur_beat_type

    bars_list, _, _, _ = reduce(parse_measure, enumerate(part.findall("./measure")), ([], 48, 4, 4))
    return LeanScoreSpec(title=title, tempo_num=t_num, tempo_den=t_den, bars=tuple(bars_list))


def _strip_ly_comments(text: str) -> str:
    no_block = re.sub(r"%\{.*?%\}", " ", text, flags=re.DOTALL)
    return re.sub(r"%[^\n]*", "", no_block)


def _extract_brace_block(text: str, open_idx: int) -> tuple[str, int]:
    """Return content inside `{ ... }` starting at `open_idx` using pure reduce scan."""
    if open_idx < 0 or open_idx >= len(text) or text[open_idx] != "{":
        return "", open_idx

    def step(acc: tuple[int, int | None], idx_ch: tuple[int, str]) -> tuple[int, int | None]:
        depth, close_pos = acc
        if close_pos is not None:
            return depth, close_pos
        pos, ch = idx_ch
        if ch == "{":
            return depth + 1, None
        if ch == "}":
            next_d = depth - 1
            return (0, pos) if next_d == 0 else (next_d, None)
        return depth, None

    _, close_pos = reduce(step, enumerate(text[open_idx:], start=open_idx), (0, None))
    end = close_pos if close_pos is not None else len(text) - 1
    return text[open_idx + 1 : end], end + 1


def _extract_primary_ly_music(clean_ly: str) -> str:
    """Locate the main Staff/Voice music block inside a LilyPond file."""
    score_m = re.search(r"\\score\s*\{", clean_ly)
    scope = _extract_brace_block(clean_ly, score_m.end() - 1)[0] if score_m else clean_ly
    # Drop trailing \layout { ... } and \midi { ... } inside \score
    scope = re.sub(r"\\midi\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", " ", scope)
    scope = re.sub(r"\\layout\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", " ", scope)
    staff_m = re.search(r"(?:\\new\s+(?:Staff|Voice)[^{]*\{|\{)", scope)
    if staff_m:
        body, _ = _extract_brace_block(scope, staff_m.end() - 1)
        # Check if outer braces wrapped another \new Staff / \fixed / \relative
        inner_m = re.search(r"(?:\\fixed\s+\S+|\\relative(?:\s+\S+)?|\\new\s+Voice[^{]*)\s*\{", body)
        if inner_m and inner_m.start() < 80:
            inner_body, _ = _extract_brace_block(body, inner_m.end() - 1)
            return inner_body
        return body
    return scope


def _ly_duration_to_ticks(dur_str: str | None, dots: str | None, mul_n: str | None, mul_d: str | None, last_ticks: int) -> int:
    if dur_str is None:
        return last_ticks
    if dur_str == "\\breve":
        base = Fraction(2 * TICKS_PER_WHOLE, 1)
    else:
        base = Fraction(TICKS_PER_WHOLE, max(1, int(dur_str)))
    if dots == "..":
        base = base * Fraction(7, 4)
    elif dots == ".":
        base = base * Fraction(3, 2)
    if mul_n is not None:
        base = base * Fraction(int(mul_n), int(mul_d) if mul_d else 1)
    return max(1, int(round(float(base))))


def _ly_pitch_token_to_midi(letter: str, accs: str, oct_marks: str) -> int:
    alter = 0
    if accs:
        alter = accs.count("is") - accs.count("es")
        if alter == 0:
            # Handle Dutch shorthand 's' / 'f' if used
            alter = accs.count("s") - accs.count("f")
    base_oct = 3 + oct_marks.count("'") - oct_marks.count(",")
    return 12 * (base_oct + 1) + _LY_LETTER_TO_SEMITONE[letter] + alter


def spec_from_lilypond_file(ly_path: Path) -> LeanScoreSpec:
    """Independently parse a written GNU LilyPond `.ly` file on disk into a LeanScoreSpec."""
    ly_path = Path(ly_path)
    raw = ly_path.read_text(encoding="utf-8")
    title_m = re.search(r'title\s*=\s*"([^"]+)"', raw)
    title = title_m.group(1).strip() if title_m else ly_path.stem

    clean = _strip_ly_comments(raw)
    tempo_m = re.search(r'\\tempo\s+(?:"[^"]*"\s*)?(?:(\d+)(\.)?\s*=\s*)?(\d+(?:\.\d+)?)(?:/(\d+))?', clean)
    if tempo_m:
        unit_val = int(tempo_m.group(1)) if tempo_m.group(1) else 4
        unit_q = Fraction(4, unit_val) * (Fraction(3, 2) if tempo_m.group(2) else 1)
        bpm_num = float(tempo_m.group(3)) / (float(tempo_m.group(4)) if tempo_m.group(4) else 1.0)
        q_bpm = bpm_num * float(unit_q)
    else:
        q_bpm = 100.0
    t_num, t_den = float_to_ratio(q_bpm)

    music_body = _extract_primary_ly_music(clean)
    # Tokenize keeping chord brackets `< ... >dur~` together and stripping markup/commands
    tok_re = re.compile(
        r'\\(?:time\s+\d+/\d+|bar\s+"[^"]*"|key\s+\S+\s+\\\S+|clef\s+(?:"[^"]+"|\S+)|mark\s+\\markup\s+\\box\s+"[^"]*"|tempo\s+(?:"[^"]*"\s*)?(?:\d+\.?\s*=\s*)?\d+(?:\.\d+)?(?:/\d+)?|\S+)|<[^>]+>[^\s|]*|\||\S+'
    )
    tokens = tok_re.findall(music_body)

    # Fold state: (bars, cur_events, beats, beat_type, last_ticks, pending_tie_pitches, has_barlines)
    InitState = tuple[list[LeanBar], list[LeanEvent], int, int, int, tuple[int, ...] | None, bool]

    def flush_bar(st: InitState) -> InitState:
        bars_out, cur_evs, beats, btype, last_t, pend_tie, has_bars = st
        if not cur_evs:
            return st
        bar_num = len(bars_out) + 1
        bar = LeanBar(bar_num, beats, btype, expected_bar_ticks(beats, btype), tuple(cur_evs))
        return [*bars_out, bar], [], beats, btype, last_t, pend_tie, has_bars

    def step_tok(st: InitState, tok: str) -> InitState:
        bars_out, cur_evs, beats, btype, last_t, pend_tie, has_bars = st
        if tok.startswith("\\time"):
            m = re.search(r"(\d+)/(\d+)", tok)
            if m:
                return bars_out, cur_evs, max(1, int(m.group(1))), max(1, int(m.group(2))), last_t, pend_tie, has_bars
            return st
        if tok == "|" or tok.startswith("\\bar"):
            if tok.startswith("\\bar") and "|." in tok and not cur_evs:
                return bars_out, cur_evs, beats, btype, last_t, pend_tie, True
            st_bars, st_cur, st_b, st_bt, st_lt, st_pt, _ = st
            return flush_bar((st_bars, st_cur, st_b, st_bt, st_lt, st_pt, True))
        if tok.startswith("\\"):
            # Skip styling/clef/key/cadenza commands that carry no duration events
            return st

        mc = _LY_CHORD_RE.match(tok)
        if mc:
            inner, d_str, dots, mn, md, tie_sym = mc.groups()
            ticks = _ly_duration_to_ticks(d_str, dots, mn, md, last_t)
            chord_notes = tuple(
                sorted(
                    set(
                        map(
                            lambda m: _ly_pitch_token_to_midi(m.group(1), m.group(2), m.group(3)),
                            filter(
                                None,
                                map(lambda p: _LY_NOTE_RE.match(p), inner.strip().split()),
                            ),
                        )
                    )
                )
            )
            tie_start = bool(tie_sym)
            tie_stop = pend_tie is not None and pend_tie == chord_notes
            ev = LeanEvent("N", ticks, tie_start, tie_stop, chord_notes)
            return bars_out, [*cur_evs, ev], beats, btype, ticks, (chord_notes if tie_start else None), has_bars

        mr = _LY_REST_RE.match(tok)
        if mr:
            d_str, dots, mn, md = mr.groups()
            ticks = _ly_duration_to_ticks(d_str, dots, mn, md, last_t)
            ev = LeanEvent("R", ticks, False, False, ())
            return bars_out, [*cur_evs, ev], beats, btype, ticks, None, has_bars

        mn_m = _LY_NOTE_RE.match(tok)
        if mn_m:
            letter, accs, octm, d_str, dots, mn, md, tie_sym = mn_m.groups()
            ticks = _ly_duration_to_ticks(d_str, dots, mn, md, last_t)
            midi = _ly_pitch_token_to_midi(letter, accs, octm)
            pitches = (midi,)
            tie_start = bool(tie_sym)
            tie_stop = pend_tie is not None and pend_tie == pitches
            ev = LeanEvent("N", ticks, tie_start, tie_stop, pitches)
            return bars_out, [*cur_evs, ev], beats, btype, ticks, (pitches if tie_start else None), has_bars

        return st

    final_st = reduce(step_tok, tokens, ([], [], 4, 4, TICKS_PER_QUARTER, None, False))
    bars_out, cur_evs, beats, btype, _, _, has_bars = flush_bar(final_st)
    if not has_bars and not bars_out and cur_evs:
        bars_out = list(_events_to_bars(cur_evs, beats, btype, pad_final_bar=False))
    return LeanScoreSpec(title=title, tempo_num=t_num, tempo_den=t_den, bars=tuple(bars_out))


def sounding_notes_from_midi_file(
    mid_path: Path,
    lane: int = 0,
    ignore_initial_beats: float = 0.0,
) -> tuple[tuple[LeanSoundingNote, ...], int, int]:
    """Independently parse a Standard MIDI `.mid` file into canonical SoundingNotes + `(tempoNum, tempoDen)`."""
    mid = mido.MidiFile(str(mid_path))
    tpq = max(1, int(mid.ticks_per_beat))

    # Extract first set_tempo across all tracks
    all_msgs = chain.from_iterable(mid.tracks)
    first_tempo = next(filter(lambda m: m.type == "set_tempo", all_msgs), None)
    if first_tempo is not None and first_tempo.tempo > 0:
        bpm_val = float(Fraction(60_000_000, int(first_tempo.tempo)))
    else:
        bpm_val = 100.0
    t_num, t_den = float_to_ratio(bpm_val)

    note_tracks = tuple(
        filter(
            lambda tr: any(map(lambda msg: msg.type == "note_on" and msg.velocity > 0, tr)),
            mid.tracks,
        )
    )
    if not note_tracks:
        return (), t_num, t_den
    track = note_tracks[min(lane, len(note_tracks) - 1)]

    # Reconstruct (onset_tpq, dur_tpq, midi_pitch) intervals via reduce
    def step_midi(
        acc: tuple[int, dict[int, int], list[tuple[int, int, int]]],
        msg: mido.Message,
    ) -> tuple[int, dict[int, int], list[tuple[int, int, int]]]:
        now, active, closed = acc
        t = now + int(msg.time)
        if msg.type == "note_on" and msg.velocity > 0:
            nxt_active = {**active, int(msg.note): t}
            return t, nxt_active, closed
        if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            pitch = int(msg.note)
            if pitch in active:
                onset = active[pitch]
                nxt_active = dict(filter(lambda kv: kv[0] != pitch, active.items()))
                dur = max(0, t - onset)
                return t, nxt_active, ([*closed, (onset, dur, pitch)] if dur > 0 else closed)
        return t, active, closed

    _, _, raw_notes = reduce(step_midi, track, (0, {}, []))

    shift_tpq = int(round(max(0.0, float(ignore_initial_beats)) * tpq))
    filtered = sorted(
        map(
            lambda r: (
                int(round(float(Fraction((r[0] - shift_tpq) * TICKS_PER_QUARTER, tpq)))),
                int(round(float(Fraction(r[1] * TICKS_PER_QUARTER, tpq)))),
                r[2],
            ),
            filter(lambda r: r[0] >= shift_tpq, raw_notes),
        )
    )

    sounding = tuple(
        map(
            lambda grp: LeanSoundingNote(
                ticks=int(grp[0][1]),
                pitches=tuple(sorted(set(map(lambda item: item[2], grp[1])))),
            ),
            groupby(filtered, key=lambda item: (item[0], item[1])),
        )
    )
    return sounding, t_num, t_den


# ------------------------------------------------------------ Lean bundle & kernel execution


def _format_score_entry(
    name: str,
    spec: LeanScoreSpec,
    aug_factor: int = 1,
    speed_num: int = 1,
    speed_den: int = 1,
) -> tuple[str, ...]:
    header = f"SCORE|{name}|{spec.tempo_num}|{spec.tempo_den}|{aug_factor}|{speed_num}|{speed_den}"

    def fmt_event(ev: LeanEvent) -> str:
        pitches_s = ",".join(map(str, ev.pitches))
        ts = "1" if ev.tie_start else "0"
        tst = "1" if ev.tie_stop else "0"
        return f"EV|{ev.kind}|{ev.ticks}|{ts}|{tst}|{pitches_s}"

    def fmt_bar(b: LeanBar) -> tuple[str, ...]:
        b_head = f"BAR|{b.bar_number}|{b.beats}|{b.beat_type}|{b.expected_ticks}"
        return (b_head, *map(fmt_event, b.events))

    return (header, *chain.from_iterable(map(fmt_bar, spec.bars)))


def _format_notes_entry(
    name: str,
    notes: Sequence[LeanSoundingNote],
    aug_factor: int = 1,
    speed_num: int = 1,
    speed_den: int = 1,
    tempo_num: int = 0,
    tempo_den: int = 1,
) -> tuple[str, ...]:
    header = f"NOTES|{name}|{aug_factor}|{speed_num}|{speed_den}|{tempo_num}|{tempo_den}"
    body = tuple(map(lambda n: f"SN|{n.ticks}|{','.join(map(str, n.pitches))}", notes))
    return (header, *body)


def serialize_bundle(
    reference: tuple[str, LeanScoreSpec],
    score_entries: Sequence[tuple[str, LeanScoreSpec, int, int, int]] = (),
    note_entries: Sequence[tuple[str, Sequence[LeanSoundingNote], int, int, int, int, int]] = (),
) -> str:
    """Serialize reference + candidate scores/MIDI streams into `score_verifier` pipe format."""
    ref_name, ref_spec = reference
    lines = [
        *_format_score_entry(ref_name, ref_spec, 1, 1, 1),
        *chain.from_iterable(map(lambda item: _format_score_entry(*item), score_entries)),
        *chain.from_iterable(map(lambda item: _format_notes_entry(*item), note_entries)),
    ]
    return "\n".join(lines) + "\n"


def _lean_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _spec_to_lean_literal(spec: LeanScoreSpec) -> str:
    def fmt_ev(ev: LeanEvent) -> str:
        kind = ".note" if ev.kind == "N" else ".rest"
        pitches = "[" + ", ".join(map(str, ev.pitches)) + "]"
        ts = "true" if ev.tie_start else "false"
        tst = "true" if ev.tie_stop else "false"
        return f"{{ kind := {kind}, pitches := {pitches}, ticks := {ev.ticks}, tieStart := {ts}, tieStop := {tst} }}"

    def fmt_bar(b: LeanBar) -> str:
        evs = "[" + ", ".join(map(fmt_ev, b.events)) + "]"
        return (
            f"{{ barNumber := {b.bar_number}, beats := {b.beats}, beatType := {b.beat_type}, "
            f"expectedTicks := {b.expected_ticks}, events := {evs} }}"
        )

    bars_str = "[" + ",\n    ".join(map(fmt_bar, spec.bars)) + "]"
    return (
        f"{{ title := \"{_lean_escape(spec.title)}\", tempoBpmNum := {spec.tempo_num}, "
        f"tempoBpmDen := {spec.tempo_den}, bars := {bars_str} }}"
    )


def generate_lean_certificate(
    out_path: Path,
    ref_name: str,
    ref_spec: LeanScoreSpec,
    other_specs: Sequence[tuple[str, LeanScoreSpec, int]] = (),
) -> Path:
    """Write a standalone `<stem>_cert.lean` module proven via kernel `decide` (zero native_decide)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    safe_ref = re.sub(r"[^A-Za-z0-9_]", "_", ref_name)

    def build_spec_block(pair: tuple[str, LeanScoreSpec, int]) -> str:
        name, spec, aug = pair
        sname = re.sub(r"[^A-Za-z0-9_]", "_", name)
        target = f"(SheetMusic.augmentScore {aug} refSpec)" if aug > 1 else "refSpec"
        return (
            f"def {sname}Spec : SheetMusic.ScoreSpec :=\n  {_spec_to_lean_literal(spec)}\n\n"
            f"theorem {sname}_equiv_ref : SheetMusic.ScoreEquiv {target} {sname}Spec :=\n"
            f"  (SheetMusic.checkScoreEquiv_iff {target} {sname}Spec).mp (by decide)\n"
        )

    other_blocks = "\n".join(map(build_spec_block, other_specs))
    content = (
        "import SheetMusic\n\n"
        f"-- Standalone machine-checked certificate for {_lean_escape(ref_spec.title)}\n"
        f"def refSpec : SheetMusic.ScoreSpec :=\n  {_spec_to_lean_literal(ref_spec)}\n\n"
        f"theorem {safe_ref}_all_bars_valid : SheetMusic.AllBarsValid refSpec.bars :=\n"
        "  (SheetMusic.checkAllBarsValid_iff refSpec.bars).mp (by decide)\n\n"
        + other_blocks
        + f"\n-- <!-- APAF Bioinformatics | {out_path.name} | Approved | 2026-11-15 -->\n"
    )
    out_path.write_text(content, encoding="utf-8")
    return out_path


def run_lean_certificate_check(cert_path: Path, timeout_sec: float = 45.0) -> tuple[bool, str]:
    """Run `lake env lean <cert_path>` so the Lean 4 kernel directly verifies the certificate."""
    env = {**os.environ, "PATH": f"{Path.home() / '.elan' / 'bin'}:/opt/homebrew/bin:{os.environ.get('PATH', '')}"}
    lake = shutil.which("lake", path=env["PATH"])
    if not lake:
        return False, "lake executable not found on PATH"
    proc = subprocess.run(
        [lake, "env", "lean", str(Path(cert_path).resolve())],
        cwd=str(LEAN_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return proc.returncode == 0, output


def ensure_verifier_built() -> Path:
    """Return path to `score_verifier` binary, building via `lake build` if missing."""
    if SCORE_VERIFIER_BIN.is_file():
        return SCORE_VERIFIER_BIN
    env = {**os.environ, "PATH": f"{Path.home() / '.elan' / 'bin'}:/opt/homebrew/bin:{os.environ.get('PATH', '')}"}
    lake = shutil.which("lake", path=env["PATH"])
    if not lake:
        raise FileNotFoundError("lake executable not found; cannot build score_verifier")
    subprocess.run([lake, "build", "score_verifier"], cwd=str(LEAN_DIR), env=env, check=True)
    return SCORE_VERIFIER_BIN


def verify_bundle_with_lean(
    reference: tuple[str, LeanScoreSpec],
    score_entries: Sequence[tuple[str, LeanScoreSpec, int, int, int]] = (),
    note_entries: Sequence[tuple[str, Sequence[LeanSoundingNote], int, int, int, int, int]] = (),
    cert_path: Path | None = None,
    timeout_sec: float = 30.0,
) -> dict[str, Any]:
    """Execute compiled Lean `score_verifier` (and optional `.lean` kernel cert) on a score bundle."""
    verifier = ensure_verifier_built()
    bundle_text = serialize_bundle(reference, score_entries=score_entries, note_entries=note_entries)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as tmp:
        tmp.write(bundle_text)
        tmp_path = Path(tmp.name)
    try:
        proc = subprocess.run(
            [str(verifier), "--input", str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    try:
        report = json.loads(proc.stdout.strip()) if proc.stdout.strip() else {
            "ok": False,
            "all_bars_valid": False,
            "failures": [proc.stderr.strip() or f"score_verifier exited {proc.returncode}"],
        }
    except json.JSONDecodeError as exc:
        report = {
            "ok": False,
            "all_bars_valid": False,
            "failures": [f"Invalid JSON from score_verifier: {exc}: {proc.stdout[:200]}"],
        }

    report["verifier_returncode"] = proc.returncode
    if cert_path is not None:
        other_for_cert = tuple(map(lambda item: (item[0], item[1], item[2]), score_entries))
        generated = generate_lean_certificate(cert_path, reference[0], reference[1], other_for_cert)
        cert_ok, cert_msg = run_lean_certificate_check(generated)
        report["lean_cert_path"] = str(generated)
        report["lean_cert_ok"] = cert_ok
        if cert_msg:
            report["lean_cert_output"] = cert_msg
        if not cert_ok:
            report["ok"] = False
            report.setdefault("failures", []).append(f"Lean kernel certificate failed: {cert_msg}")
    return report


# <!-- APAF Bioinformatics | lean_bridge.py | Approved | 2026-11-15 -->
