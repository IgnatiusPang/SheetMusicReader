"""Karaoke Note, Word & Background Music Trainer generator and score extractor.

Extracts chords, aligned syllables, cue pickups, and melody notes from vector PDFs
(or psalm JSON dictionaries) and renders an interactive standalone HTML5 Karaoke
Sing-Along Trainer featuring:
- Live word-by-word karaoke teleprompter with active note/pitch cue right next to the words
- Synchronized 5-line treble staff notation (Rule 2 & Rule 3 layout) with moving playhead
- Web Audio lookahead synthesizer for background chord accompaniment, vocal guide, count-in, and beat clicks
- Speed presets (100%, 75%, 50%, 33%, 25%), transposition, looping, and section/arrangement selector
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import replace
from fractions import Fraction
from functools import reduce
from html import escape as html_escape
from itertools import chain
from pathlib import Path
from typing import Any, Sequence

import pdfplumber

import lean_bridge
import score_formatter
import vector_omr
from audio_synth import AudioEvent

STEP_TO_SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
FIFTHS_TO_KEY_NAME = {
    0: "C Major", 1: "G Major", 2: "D Major", 3: "A Major", 4: "E Major",
    5: "B Major", 6: "F# Major", 7: "C# Major",
    -1: "F Major", -2: "Bb Major", -3: "Eb Major", -4: "Ab Major",
    -5: "Db Major", -6: "Gb Major", -7: "Cb Major",
}
FIFTHS_TO_KEY_SIG = {
    0: "0", 1: "1#", 2: "2#", 3: "3#", 4: "4#", 5: "5#", 6: "6#", 7: "7#",
    -1: "1b", -2: "2b", -3: "3b", -4: "4b", -5: "5b", -6: "6b", -7: "7b",
}

OPUS_CHORD_SUBS = (
    ("\u201e\u02c6\u02c6", "add"),
    ("\u0152\u201e\u0160", "maj"),
    ("\u201c", "sus"),
    ("\u2039", "m"),
    ("\u00a9", "#"),
    ("\u00a8", "b"),
)

CHORD_REGEX = re.compile(
    r"^\s*([A-G])([#b]?)"
    r"(\(?(?:maj7|maj9|maj|min7|min|m7|m9|m6|m|sus4|sus2|sus|add2|add9|add4|dim7|dim|aug|7|6|9|2|4|5|b5|#5|#4)?\)?"
    r"(?:\((?:sus4|sus2|add2|add9|add4|b5|#5|#4|2|4|9)\))?)"
    r"(?:/([A-G][#b]?))?\s*$"
)


def clean_chord_symbol(raw: str) -> str:
    """Decode Sibelius OpusChords / Bravura / plain chord glyphs to readable ASCII."""
    cleaned = reduce(lambda s, kv: s.replace(kv[0], kv[1]), OPUS_CHORD_SUBS, str(raw or "").strip())
    return re.sub(r"\s+", "", cleaned)


def _note_token_to_pc(token: str) -> int | None:
    if not token:
        return None
    letter = token[0].upper()
    if letter not in STEP_TO_SEMI:
        return None
    alter = token[1:].count("#") - token[1:].count("b")
    return (STEP_TO_SEMI[letter] + alter) % 12


def _midi_near_register(pc: int, low: int, high: int) -> int:
    candidates = tuple(filter(lambda m: low <= m <= high, range(pc, 128, 12)))
    if candidates:
        return candidates[len(candidates) // 2]
    above = next(filter(lambda m: m >= low, range(pc, 128, 12)), 60 + pc)
    return above


def parse_chord_voicing(symbol: str) -> dict[str, Any] | None:
    """Parse a chord symbol like `'G'`, `'F/G'`, `'D(sus4)'`, `'Am7'`, `'C(add2)'` into MIDI voicing."""
    clean_sym = clean_chord_symbol(symbol)
    if not clean_sym:
        return None
    m = CHORD_REGEX.match(clean_sym)
    if not m:
        return None
    root_tok = m.group(1) + (m.group(2) or "")
    qual = (m.group(3) or "").lower().replace("(", "").replace(")", "")
    slash_tok = m.group(4)

    root_pc = _note_token_to_pc(root_tok)
    if root_pc is None:
        return None

    bass_pc = _note_token_to_pc(slash_tok) if slash_tok else root_pc
    bass_midi = _midi_near_register(bass_pc if bass_pc is not None else root_pc, 38, 49)

    if qual in ("sus4", "sus"):
        intervals = (0, 5, 7)
    elif qual == "sus2":
        intervals = (0, 2, 7)
    elif qual in ("m", "min"):
        intervals = (0, 3, 7)
    elif qual in ("m7", "min7"):
        intervals = (0, 3, 7, 10)
    elif qual == "maj7":
        intervals = (0, 4, 7, 11)
    elif qual == "7":
        intervals = (0, 4, 7, 10)
    elif qual in ("add2", "add9", "2"):
        intervals = (0, 2, 4, 7)
    elif qual in ("add4", "4"):
        intervals = (0, 4, 5, 7)
    elif qual == "6":
        intervals = (0, 4, 7, 9)
    elif qual == "m6":
        intervals = (0, 3, 7, 9)
    elif qual in ("dim", "dim7"):
        intervals = (0, 3, 6)
    elif qual == "aug":
        intervals = (0, 4, 8)
    else:
        intervals = (0, 4, 7)

    raw_pcs = tuple(map(lambda iv: (root_pc + iv) % 12, intervals))
    chord_midis = tuple(sorted(set(map(lambda pc: _midi_near_register(pc, 53, 66), raw_pcs))))
    return {
        "symbol": clean_sym,
        "bass_midi": int(bass_midi),
        "chord_midis": list(chord_midis),
    }


def _midi_to_pitch_name(midi: int, fifths: int = 0) -> str:
    sharps = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    flats = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
    table = flats if fifths < 0 else sharps
    octv = (int(midi) // 12) - 1
    return f"{table[int(midi) % 12]}{octv}"


def _xml_type_from_quarters(val_q: float) -> tuple[str, bool]:
    ticks = max(1, lean_bridge.quarters_to_ticks(val_q))
    return score_formatter._ticks_to_xml_type(ticks)


def _split_compound_word(w: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    txt = str(w["text"]).strip()
    if txt in ("-", "—", "–") or "-" not in txt or txt.startswith("-") or txt.endswith("-"):
        return (w,)
    parts = tuple(filter(None, txt.split("-")))
    if len(parts) <= 1:
        return (w,)
    n = len(parts)
    x0 = float(w["x0"])
    span = max(1.0, float(w["x1"]) - x0)
    return tuple(
        map(
            lambda ip: {
                **w,
                "x0": x0 + (span * ip[0]) / n,
                "x1": x0 + (span * (ip[0] + 1)) / n,
                "text": ip[1] + ("-" if ip[0] < n - 1 else ""),
            },
            enumerate(parts),
        )
    )


def _merge_hyphen_tokens(tokens: Sequence[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    def step(acc: tuple[dict[str, Any], ...], tok: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        txt = str(tok["text"]).strip()
        if txt == "-" and acc:
            prev = acc[-1]
            if not str(prev["text"]).endswith("-"):
                return (*acc[:-1], {**prev, "text": f"{prev['text']}-"})
            return acc
        if txt in ("-", "—", "–") or re.match(r"^\d+\.$", txt) or re.match(r"^Copyright", txt, re.I):
            return acc
        return (*acc, {**tok, "text": txt})

    return reduce(step, tokens, ())


def _is_music_font(fontname: str) -> bool:
    return any(map(lambda f: f in str(fontname), ("Opus", "Leland", "Bravura", "MScore")))


def _extract_system_annotations(
    sys_measures: Sequence[Any],
    page_words: Sequence[dict[str, Any]],
    staff: Any,
    next_staff_top: float | None,
) -> tuple[dict[tuple[int, int], str], dict[tuple[int, int], str], list[str]]:
    """Extract `(lyric_map, chord_map, cue_syllables)` keyed by `(measure_idx, event_idx)`."""
    top_bound = staff.top - 34.0
    above_words = sorted(
        filter(
            lambda w: top_bound <= float(w["top"]) <= staff.top + 2.0
            and (
                "Chord" in str(w.get("fontname", ""))
                or bool(CHORD_REGEX.match(clean_chord_symbol(w["text"])))
            ),
            page_words,
        ),
        key=lambda w: float(w["x0"]),
    )

    bottom_cap = min(staff.bottom + 42.0, (next_staff_top - 22.0) if next_staff_top is not None else staff.bottom + 42.0)
    below_raw = tuple(
        filter(
            lambda w: staff.bottom - 1.5 <= float(w["top"]) <= bottom_cap
            and not _is_music_font(w.get("fontname", ""))
            and not str(w["text"]).strip().startswith("Copyright"),
            page_words,
        )
    )

    min_top = min(map(lambda w: float(w["top"]), below_raw), default=staff.bottom + 12.0)
    main_raw = sorted(filter(lambda w: float(w["top"]) <= min_top + 6.0, below_raw), key=lambda w: float(w["x0"]))
    cue_raw = sorted(filter(lambda w: float(w["top"]) > min_top + 6.0, below_raw), key=lambda w: float(w["x0"]))

    main_syls = _merge_hyphen_tokens(tuple(chain.from_iterable(map(_split_compound_word, main_raw))))
    cue_syls = _merge_hyphen_tokens(tuple(chain.from_iterable(map(_split_compound_word, cue_raw))))

    flat_events = tuple(
        chain.from_iterable(
            map(
                lambda im: map(lambda ie: (im[0], ie[0], ie[1]), enumerate(im[1].events)),
                enumerate(sys_measures),
            )
        )
    )
    reg_events = tuple(filter(lambda x: not getattr(x[2], "extra", False), flat_events))
    extra_events = tuple(filter(lambda x: bool(getattr(x[2], "extra", False)), flat_events))

    # Build untied regular note onsets for monotonic syllable assignment
    def step_onset(acc: tuple[tuple[tuple[int, int, float], ...], bool], item: tuple[int, int, Any]):
        out, prev_tied = acc
        mi, ei, ev = item
        if not ev.midis:
            return out, False
        if not prev_tied:
            out = (*out, (mi, ei, float(ev.x)))
        return out, bool(ev.tie)

    onsets, _ = reduce(step_onset, reg_events, ((), False))

    def assign_syl(
        acc: tuple[dict[tuple[int, int], str], int],
        idx_syl: tuple[int, dict[str, Any]],
    ) -> tuple[dict[tuple[int, int], str], int]:
        mapping, min_idx = acc
        s_idx, syl = idx_syl
        if not onsets or min_idx >= len(onsets):
            return mapping, min_idx
        rem_syls = len(main_syls) - s_idx
        max_idx = max(min_idx, len(onsets) - rem_syls)
        target_x = float(syl["x0"]) + 3.5
        best_i = min(range(min_idx, max_idx + 1), key=lambda idx: abs(onsets[idx][2] - target_x))
        mi, ei, _ = onsets[best_i]
        return {**mapping, (mi, ei): str(syl["text"])}, best_i + 1

    lyric_map, _ = reduce(assign_syl, enumerate(main_syls), ({}, 0))

    # Assign cue syllables onto `extra` noteheads (e.g. "2. Je-" pickup in Bar 4)
    def assign_cue(
        mapping: dict[tuple[int, int], str],
        idx_item: tuple[int, tuple[int, int, Any]],
    ) -> dict[tuple[int, int], str]:
        idx, (mi, ei, _) = idx_item
        if idx < len(cue_syls):
            return {**mapping, (mi, ei): str(cue_syls[idx]["text"])}
        return mapping

    cue_note_events = tuple(filter(lambda x: bool(x[2].midis), extra_events))
    lyric_map = reduce(assign_cue, enumerate(cue_note_events), lyric_map)

    # Assign chord symbols above the staff onto the nearest event in the system
    def assign_chord(
        mapping: dict[tuple[int, int], str],
        w: dict[str, Any],
    ) -> dict[tuple[int, int], str]:
        sym = clean_chord_symbol(w["text"])
        if not parse_chord_voicing(sym) or not reg_events:
            return mapping
        cx = float(w["x0"])
        best_ev = min(reg_events, key=lambda x: abs(float(x[2].x) - cx))
        return {**mapping, (best_ev[0], best_ev[1]): sym}

    chord_map: dict[tuple[int, int], str] = reduce(assign_chord, above_words, {})
    return lyric_map, chord_map, list(map(lambda c: str(c["text"]), cue_syls))


def _annotate_system_measures(
    sys_idx: int,
    sys_staff_res: Any,
    page_words: Sequence[dict[str, Any]],
    next_staff_top: float | None,
) -> tuple[tuple[tuple[int, int, tuple[dict[str, Any], ...], tuple[int, int]], ...], list[str]]:
    """Return enriched measure tuples for one staff system `(sys_idx, time_sig, enriched_events, key_tuple)`."""
    measures = sys_staff_res.measures
    lyric_map, chord_map, cue_list = _extract_system_annotations(
        measures, page_words, sys_staff_res.staff, next_staff_top
    )

    def enrich_measure(mi_m: tuple[int, Any]) -> dict[str, Any]:
        mi, m = mi_m

        def enrich_ev(ei_ev: tuple[int, Any]) -> dict[str, Any]:
            ei, ev = ei_ev
            midis = tuple(sorted(set(map(int, getattr(ev, "midis", ())))))
            val_q = float(ev.value)
            ticks = lean_bridge.quarters_to_ticks(val_q)
            dur_name, has_dot = score_formatter._ticks_to_xml_type(ticks)
            return {
                "val_q": val_q,
                "ticks": ticks,
                "dur_name": dur_name,
                "has_dot": has_dot,
                "midis": list(midis),
                "midi": midis[0] if midis else None,
                "tie": bool(getattr(ev, "tie", False)),
                "extra": bool(getattr(ev, "extra", False)),
                "lyric": lyric_map.get((mi, ei), ""),
                "chord_symbol": chord_map.get((mi, ei), ""),
            }

        return {
            "sys_idx": sys_idx,
            "measure_idx": mi,
            "time": tuple(m.time),
            "key": int(m.key),
            "events": tuple(map(enrich_ev, enumerate(m.events))),
        }

    return tuple(map(enrich_measure, enumerate(measures))), cue_list


def _assemble_timeline_mode(
    mode_id: str,
    label: str,
    tagged_bars: Sequence[tuple[dict[str, Any], bool, bool, str]],
    tempo_qpm: float,
    key_fifths: int,
    default_chord: str,
) -> dict[str, Any]:
    """Assemble bars, word-groups, chords, and phrases for one playable timeline mode."""
    # First resolve each bar's exact event stream (applying cue pickup activation cleanly)
    def resolve_bar_events(item: tuple[dict[str, Any], bool, bool, str]) -> dict[str, Any]:
        bar_d, activate_extra, is_sec_end, sec_label = item
        raw_evs = bar_d["events"]
        reg_evs = tuple(filter(lambda e: not e["extra"], raw_evs))
        ext_evs = tuple(filter(lambda e: e["extra"], raw_evs))
        chosen = reg_evs
        if activate_extra and ext_evs and reg_evs:
            ext_ticks = sum(map(lambda e: int(e["ticks"]), ext_evs))
            last_reg = reg_evs[-1]
            if not last_reg["midis"] and int(last_reg["ticks"]) >= ext_ticks:
                rem_ticks = int(last_reg["ticks"]) - ext_ticks
                if rem_ticks > 0:
                    rem_q = float(rem_ticks) / float(lean_bridge.TICKS_PER_QUARTER)
                    rem_type, rem_dot = score_formatter._ticks_to_xml_type(rem_ticks)
                    rem_rest = {
                        **last_reg,
                        "val_q": rem_q,
                        "ticks": rem_ticks,
                        "dur_name": rem_type,
                        "has_dot": rem_dot,
                    }
                    chosen = (*reg_evs[:-1], rem_rest, *ext_evs)
                else:
                    chosen = (*reg_evs[:-1], *ext_evs)
        if is_sec_end and chosen and chosen[-1]["tie"]:
            chosen = (*chosen[:-1], {**chosen[-1], "tie": False})
        return {
            "sys_idx": bar_d["sys_idx"],
            "time": bar_d["time"],
            "key": bar_d["key"],
            "section_label": sec_label,
            "events": chosen,
        }

    resolved_bars = tuple(map(resolve_bar_events, tagged_bars))

    # Flatten across bars while propagating tie_start/tie_stop, onset_q, active_chord, and word cues
    def step_bar(acc, idx_bar: tuple[int, dict[str, Any]]):
        bars_out, flat_evs, cursor_q, open_tie_midi, cur_chord, cur_word = acc
        bar_idx, b = idx_bar
        bar_start_q = cursor_q

        def step_ev(ev_acc, ev: dict[str, Any]):
            b_evs, f_evs, ev_q, tie_midi, c_sym, active_w = ev_acc
            c_sym = ev["chord_symbol"] or c_sym or default_chord
            dur_q = float(ev["ticks"]) / float(lean_bridge.TICKS_PER_QUARTER)
            is_note = bool(ev["midis"])
            ev_midi = int(ev["midis"][0]) if is_note else None
            t_stop = bool(is_note and tie_midi is not None and ev_midi == tie_midi)
            t_start = bool(is_note and ev["tie"])
            next_tie = ev_midi if t_start else None

            raw_lyr = str(ev["lyric"] or "").strip()
            if raw_lyr and raw_lyr not in ("—", "–"):
                next_word = raw_lyr
            elif is_note and t_stop:
                next_word = active_w
            elif is_note and active_w:
                next_word = active_w
            else:
                next_word = ""

            ev_idx = len(f_evs)
            pitch_nm = _midi_to_pitch_name(ev_midi, b["key"]) if ev_midi is not None else "REST"
            ev_obj = {
                "event_index": ev_idx,
                "bar_number": bar_idx + 1,
                "system_index": b["sys_idx"],
                "section_label": b["section_label"],
                "kind": "N" if is_note else "R",
                "midi": ev_midi,
                "pitches": ev["midis"],
                "pitch_name": pitch_nm,
                "onset_q": round(ev_q, 6),
                "dur_q": round(dur_q, 6),
                "sound_dur_q": round(dur_q, 6),
                "ticks": int(ev["ticks"]),
                "duration": ev["dur_name"],
                "has_dot": bool(ev["has_dot"]),
                "tie_start": t_start,
                "tie_stop": t_stop,
                "lyric": raw_lyr,
                "active_word": raw_lyr or (active_w if is_note else ""),
                "chord_symbol": c_sym,
            }
            return (*b_evs, ev_obj), (*f_evs, ev_obj), ev_q + dur_q, next_tie, c_sym, (next_word if is_note else "")

        b_evs, flat_evs, next_q, open_tie_midi, cur_chord, cur_word = reduce(
            step_ev, b["events"], ((), flat_evs, cursor_q, open_tie_midi, cur_chord, cur_word)
        )
        bar_obj = {
            "bar_number": bar_idx + 1,
            "system_index": b["sys_idx"],
            "section_label": b["section_label"],
            "beats": int(b["time"][0]),
            "beat_type": int(b["time"][1]),
            "start_q": round(bar_start_q, 6),
            "dur_q": round(next_q - bar_start_q, 6),
            "events": list(b_evs),
        }
        return (*bars_out, bar_obj), flat_evs, next_q, open_tie_midi, cur_chord, cur_word

    bars_built, flat_evs, total_q, _, _, _ = reduce(
        step_bar, enumerate(resolved_bars), ((), (), 0.0, None, default_chord, "")
    )

    # Compute merged sound_dur_q across ties backwards so each tie-start holds total duration
    def back_tie_step(acc: tuple[float, list[dict[str, Any]]], ev: dict[str, Any]):
        tie_extra, out = acc
        if ev["tie_start"] and tie_extra > 0.0:
            merged_d = round(ev["dur_q"] + tie_extra, 6)
            ev2 = {**ev, "sound_dur_q": merged_d}
            return (merged_d if ev["tie_stop"] else 0.0), [ev2, *out]
        if ev["tie_stop"]:
            return float(ev["dur_q"]), [ev, *out]
        return 0.0, [ev, *out]

    _, flat_with_ties = reduce(back_tie_step, reversed(flat_evs), (0.0, []))
    tie_dur_by_idx = dict(map(lambda e: (e["event_index"], e["sound_dur_q"]), flat_with_ties))

    # Refresh sound_dur_q inside bars
    bars_final = list(
        map(
            lambda b: {
                **b,
                "events": list(map(lambda e: {**e, "sound_dur_q": tie_dur_by_idx[e["event_index"]]}, b["events"])),
            },
            bars_built,
        )
    )
    all_evs = tuple(chain.from_iterable(map(lambda b: b["events"], bars_final)))

    # Group bars into system phrases (contiguous runs of same (section_label, system_index) or max ~5 bars)
    def step_phrase_bars(acc: list[list[dict[str, Any]]], b: dict[str, Any]) -> list[list[dict[str, Any]]]:
        if acc and acc[-1][-1]["system_index"] == b["system_index"] and acc[-1][-1]["section_label"] == b["section_label"]:
            return [*acc[:-1], [*acc[-1], b]]
        return [*acc, [b]]

    bar_groups = reduce(step_phrase_bars, bars_final, [])

    # Build word list from events cleanly: each note with a non-empty lyric starts a karaoke word;
    # subsequent notes without a new lyric extend the previous word's end_q across ties/melismas.
    def collect_phrase_words(phrase_evs: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        def step_w(acc: list[dict[str, Any]], ev: dict[str, Any]) -> list[dict[str, Any]]:
            ev_end = round(ev["onset_q"] + ev["dur_q"], 6)
            if ev["kind"] == "R":
                return acc
            lyr = str(ev["lyric"] or "").strip()
            if lyr and lyr not in ("—", "–"):
                w_obj = {
                    "word_index": len(acc),
                    "text": lyr,
                    "pitch_name": ev["pitch_name"],
                    "midi": ev["midi"],
                    "start_q": ev["onset_q"],
                    "end_q": ev_end,
                    "event_indices": [ev["event_index"]],
                }
                return [*acc, w_obj]
            if acc:
                prev = acc[-1]
                return [
                    *acc[:-1],
                    {
                        **prev,
                        "end_q": ev_end,
                        "event_indices": [*prev["event_indices"], ev["event_index"]],
                    },
                ]
            return acc

        return reduce(step_w, phrase_evs, [])

    def build_phrase(idx_grp: tuple[int, list[dict[str, Any]]]) -> dict[str, Any]:
        p_idx, p_bars = idx_grp
        p_evs = list(chain.from_iterable(map(lambda b: b["events"], p_bars)))
        words = collect_phrase_words(p_evs)
        return {
            "phrase_index": p_idx,
            "section_label": p_bars[0]["section_label"],
            "bar_start": p_bars[0]["bar_number"],
            "bar_end": p_bars[-1]["bar_number"],
            "start_q": p_bars[0]["start_q"],
            "end_q": round(p_bars[-1]["start_q"] + p_bars[-1]["dur_q"], 6),
            "bars": p_bars,
            "words": words,
        }

    phrases = list(map(build_phrase, enumerate(bar_groups)))

    # Assign word_index onto each note event cleanly so word<->note highlighting stays 1:1
    ev_to_word = dict(
        chain.from_iterable(
            map(
                lambda p: chain.from_iterable(
                    map(
                        lambda w: map(lambda ei: (ei, w["text"]), w["event_indices"]),
                        p["words"],
                    )
                ),
                phrases,
            )
        )
    )
    phrases_synced = list(
        map(
            lambda p: {
                **p,
                "bars": list(
                    map(
                        lambda b: {
                            **b,
                            "events": list(
                                map(
                                    lambda e: {
                                        **e,
                                        "active_word": ev_to_word.get(e["event_index"], e["active_word"]),
                                    },
                                    b["events"],
                                )
                            ),
                        },
                        p["bars"],
                    )
                ),
            },
            phrases,
        )
    )

    # Compress chord runs across all_evs
    def step_chord(acc: list[dict[str, Any]], ev: dict[str, Any]) -> list[dict[str, Any]]:
        sym = ev["chord_symbol"]
        voicing = parse_chord_voicing(sym)
        if not voicing:
            return acc
        ev_end = round(ev["onset_q"] + ev["dur_q"], 6)
        if acc and acc[-1]["symbol"] == voicing["symbol"] and abs(acc[-1]["end_q"] - ev["onset_q"]) < 1e-4:
            prev = acc[-1]
            return [*acc[:-1], {**prev, "end_q": ev_end, "dur_q": round(ev_end - prev["onset_q"], 6)}]
        return [
            *acc,
            {
                "symbol": voicing["symbol"],
                "onset_q": ev["onset_q"],
                "end_q": ev_end,
                "dur_q": round(ev_end - ev["onset_q"], 6),
                "bass_midi": voicing["bass_midi"],
                "chord_midis": voicing["chord_midis"],
            },
        ]

    chords_timeline = reduce(step_chord, all_evs, [])
    return {
        "mode_id": mode_id,
        "label": label,
        "total_beats_q": round(total_q, 6),
        "bar_count": len(bars_final),
        "phrases": phrases_synced,
        "chords": chords_timeline,
    }


def extract_karaoke_score_from_pdf(pdf_path: Path) -> dict[str, Any]:
    """Extract notes, aligned lyrics, chords, and playback modes from a vector sheet music PDF."""
    pdf_path = Path(pdf_path)
    sc = vector_omr.read_score(pdf_path)
    if not getattr(sc, "systems", None):
        raise ValueError(f"No vector music systems found in {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        words_by_page = tuple(
            map(
                lambda pg: pg.extract_words(
                    keep_blank_chars=False,
                    x_tolerance=1.2,
                    y_tolerance=2.0,
                    extra_attrs=["fontname", "size"],
                ),
                pdf.pages,
            )
        )

    # Extract header title & composer above first staff
    first_st = sc.systems[0][0].staff
    header_words = tuple(
        filter(
            lambda w: float(w["top"]) < first_st.top - 18.0
            and not _is_music_font(w.get("fontname", ""))
            and "Chord" not in str(w.get("fontname", "")),
            words_by_page[first_st.page],
        )
    )
    max_hdr_size = max(map(lambda w: float(w.get("size", 10.0)), header_words), default=12.0)
    title_tokens = sorted(
        filter(lambda w: float(w.get("size", 0.0)) >= max_hdr_size - 1.5, header_words),
        key=lambda w: float(w["x0"]),
    )
    title_str = " ".join(map(lambda w: str(w["text"]), title_tokens)).strip() or pdf_path.stem.replace("-", " ")

    comp_tokens = sorted(
        filter(
            lambda w: float(w.get("size", 0.0)) < max_hdr_size - 1.5
            and not re.search(r"=\s*\d+", str(w["text"]))
            and float(w["x0"]) > 300.0,
            header_words,
        ),
        key=lambda w: float(w["x0"]),
    )
    composer_str = " ".join(map(lambda w: str(w["text"]), comp_tokens)).strip()

    # Annotate all systems' lane-0 measures
    def proc_sys(si: int) -> tuple[tuple[dict[str, Any], ...], list[str]]:
        sr = sc.systems[si][0]
        next_top = (
            sc.systems[si + 1][0].staff.top
            if (si + 1 < len(sc.systems) and sc.systems[si + 1][0].staff.page == sr.staff.page)
            else None
        )
        return _annotate_system_measures(si, sr, words_by_page[sr.staff.page], next_top)

    annotated_per_sys = tuple(map(proc_sys, range(len(sc.systems))))
    sys_measures = tuple(map(lambda x: x[0], annotated_per_sys))
    all_bars_flat = tuple(chain.from_iterable(sys_measures))

    first_m = all_bars_flat[0] if all_bars_flat else {"time": (4, 4), "key": 0}
    ts_str = f"{first_m['time'][0]}/{first_m['time'][1]}"
    fifths = int(first_m["key"])
    key_name = FIFTHS_TO_KEY_NAME.get(fifths, "C Major")
    key_sig = FIFTHS_TO_KEY_SIG.get(fifths, "0")
    tempo_qpm = float(sc.tempo or 90.0)
    default_chord = next(
        chain.from_iterable(
            map(lambda e: (e["chord_symbol"],) if e["chord_symbol"] else (), chain.from_iterable(map(lambda b: b["events"], all_bars_flat)))
        ),
        "",
    )

    secs = tuple(vector_omr.sections_of(sc))
    arr = tuple(vector_omr.arrangement(sc))

    def _next_verse_starts_sounding(next_sec: Any) -> bool:
        if next_sec is None or getattr(next_sec, "kind", "") != "verse":
            return False
        nsi, nv, _ = next_sec.parts[0]
        nms = sc.systems[nsi][nv].measures if (nsi < len(sc.systems) and nv < len(sc.systems[nsi])) else ()
        if not nms:
            return False
        fev = next(filter(lambda ev: not getattr(ev, "extra", False), getattr(nms[0], "events", ())), None)
        return bool(fev is not None and getattr(fev, "midis", ()))

    def _sec_label(sec: Any, silence_flag: bool) -> str:
        if getattr(sec, "kind", "") == "response":
            return "Final Response" if silence_flag else "Response"
        if getattr(sec, "kind", "") == "final":
            return "Final"
        if getattr(sec, "kind", "") == "verse":
            return f"Verse {sec.num}"
        return "Score"

    def _bars_for_sec(sec: Any, silence_flag: bool, next_sec: Any) -> tuple[tuple[dict[str, Any], bool, bool, str], ...]:
        s_lbl = _sec_label(sec, silence_flag)
        activate_last = bool(
            not silence_flag
            and getattr(sec, "kind", "") == "response"
            and _next_verse_starts_sounding(next_sec)
        )
        sec_ms = tuple(
            chain.from_iterable(
                map(lambda p: sys_measures[p[0]] if p[0] < len(sys_measures) else (), sec.parts)
            )
        )
        last_i = len(sec_ms) - 1
        return tuple(
            map(
                lambda im: (im[1], (im[0] == last_i) and activate_last, im[0] == last_i, s_lbl),
                enumerate(sec_ms),
            )
        )

    modes: list[dict[str, Any]] = []

    if len(secs) > 1:
        arr_tagged = tuple(
            chain.from_iterable(
                map(
                    lambda isf: _bars_for_sec(
                        isf[1][0], isf[1][1], arr[isf[0] + 1][0] if isf[0] + 1 < len(arr) else None
                    ),
                    enumerate(arr),
                )
            )
        )
        modes.append(
            _assemble_timeline_mode(
                "full_arrangement", "Full Sung Psalm", arr_tagged, tempo_qpm, fifths, default_chord
            )
        )

    sys_to_sec_label = dict(
        chain.from_iterable(
            map(lambda sec: map(lambda p: (p[0], _sec_label(sec, False)), sec.parts), secs)
        )
    )
    chart_tagged = tuple(
        map(
            lambda ib: (ib[1], False, ib[0] == len(all_bars_flat) - 1, sys_to_sec_label.get(ib[1]["sys_idx"], "Chart")),
            enumerate(all_bars_flat),
        )
    )
    modes.append(
        _assemble_timeline_mode(
            "chart_as_written", "Printed Chart (Bars 1-" + str(len(all_bars_flat)) + ")", chart_tagged, tempo_qpm, fifths, default_chord
        )
    )

    if len(secs) > 1:
        def sec_mode(sec: Any) -> dict[str, Any]:
            mid = "response" if sec.kind == "response" else (f"verse_{sec.num}" if sec.kind == "verse" else sec.kind)
            lbl = _sec_label(sec, False)
            tagged = _bars_for_sec(sec, True, None)
            return _assemble_timeline_mode(mid, lbl, tagged, tempo_qpm, fifths, default_chord)

        modes.extend(map(sec_mode, secs))

    return {
        "id": f"pdf:{pdf_path.name}",
        "title": title_str,
        "composer": composer_str,
        "key": key_name,
        "key_signature": key_sig,
        "fifths": fifths,
        "time_signature": ts_str,
        "tempo_qpm": round(tempo_qpm, 2),
        "modes": modes,
    }


def extract_karaoke_from_psalm_dict(psalm_data: dict[str, Any]) -> dict[str, Any]:
    """Convert a `psalms_db` psalm dictionary into the Karaoke Trainer schema."""
    ts_raw = str(psalm_data.get("time_signature", "4/4")).split("/")
    ts_beats = max(1, int(ts_raw[0])) if len(ts_raw) == 2 else 4
    ts_type = max(1, int(ts_raw[1])) if len(ts_raw) == 2 else 4
    fifths = score_formatter._fifths_from_psalm(psalm_data)
    tempo_qpm = float(psalm_data.get("tempo", 90) or 90)
    cap_ticks = lean_bridge.expected_bar_ticks(ts_beats, ts_type)

    resp_notes = psalm_data.get("response", {}).get("notes", ())
    resp_chords = psalm_data.get("response", {}).get("chords", ())

    def note_to_ev(idx_n: tuple[int, dict[str, Any]]) -> dict[str, Any]:
        idx, n = idx_n
        ticks = lean_bridge.quarters_to_ticks(float(n.get("beats", 1.0)))
        val_q = float(ticks) / float(lean_bridge.TICKS_PER_QUARTER)
        dur_name, has_dot = score_formatter._ticks_to_xml_type(ticks)
        is_rest = bool(n.get("rest") or n.get("is_rest") or n.get("pitch") == "REST")
        midi = None if is_rest else int(n.get("midi", 60))
        chord_s = str(resp_chords[idx // 2]) if (idx // 2 < len(resp_chords) and idx % 2 == 0) else ""
        return {
            "val_q": val_q,
            "ticks": ticks,
            "dur_name": dur_name,
            "has_dot": has_dot,
            "midis": [] if midi is None else [midi],
            "midi": midi,
            "tie": n.get("tie") == "start" or bool(n.get("tied")),
            "extra": False,
            "lyric": str(n.get("lyric", "")),
            "chord_symbol": clean_chord_symbol(chord_s),
        }

    evs = tuple(map(note_to_ev, enumerate(resp_notes)))

    def chunk_bars(acc: tuple[list[list[dict[str, Any]]], list[dict[str, Any]], int], ev: dict[str, Any]):
        done, cur, cur_t = acc
        nt = cur_t + int(ev["ticks"])
        nc = [*cur, ev]
        if nt >= cap_ticks:
            return [*done, nc], [], 0
        return done, nc, nt

    done_groups, rem, rem_t = reduce(chunk_bars, evs, ([], [], 0))
    if rem:
        pad_t = cap_ticks - rem_t
        if pad_t > 0:
            pt, pd = score_formatter._ticks_to_xml_type(pad_t)
            rem = [
                *rem,
                {
                    "val_q": float(pad_t) / float(lean_bridge.TICKS_PER_QUARTER),
                    "ticks": pad_t,
                    "dur_name": pt,
                    "has_dot": pd,
                    "midis": [],
                    "midi": None,
                    "tie": False,
                    "extra": False,
                    "lyric": "",
                    "chord_symbol": "",
                },
            ]
        done_groups = [*done_groups, rem]

    tagged = tuple(
        map(
            lambda ig: (
                {
                    "sys_idx": ig[0] // 4,
                    "time": (ts_beats, ts_type),
                    "key": fifths,
                    "events": tuple(ig[1]),
                },
                False,
                ig[0] == len(done_groups) - 1,
                "Response",
            ),
            enumerate(done_groups),
        )
    )
    default_chord = clean_chord_symbol(resp_chords[0]) if resp_chords else ""
    mode = _assemble_timeline_mode("response", "Response", tagged, tempo_qpm, fifths, default_chord)
    return {
        "id": f"psalm:{psalm_data.get('id', 'score')}",
        "title": str(psalm_data.get("title", "Psalm")),
        "composer": str(psalm_data.get("composer", "")),
        "key": str(psalm_data.get("key", FIFTHS_TO_KEY_NAME.get(fifths, "C Major"))),
        "key_signature": str(psalm_data.get("key_signature", FIFTHS_TO_KEY_SIG.get(fifths, "0"))),
        "fifths": fifths,
        "time_signature": f"{ts_beats}/{ts_type}",
        "tempo_qpm": round(tempo_qpm, 2),
        "modes": [mode],
    }


def chords_to_audio_events(chords: Sequence[dict[str, Any]], time_signature: str = "4/4") -> tuple[AudioEvent, ...]:
    """Convert extracted chord timeline spans into rhythmic bass+pad AudioEvents for WAV/MP3 synthesis."""
    ts_parts = str(time_signature or "4/4").split("/")
    ts_num = max(1, int(ts_parts[0])) if len(ts_parts) == 2 else 4
    ts_den = max(1, int(ts_parts[1])) if len(ts_parts) == 2 else 4
    pulse_q = 1.5 if (ts_num in (6, 9, 12) and ts_den == 8) else (4.0 / float(ts_den))

    def expand_span(ch: dict[str, Any]) -> tuple[AudioEvent, ...]:
        onset = float(ch["onset_q"])
        dur = float(ch["dur_q"])
        if dur <= 0.05:
            return ()
        bass = int(ch["bass_midi"])
        pad = tuple(map(int, ch["chord_midis"]))
        bass_ev = AudioEvent(onset, min(dur, pulse_q * 1.9), (bass,), 0.55)
        n_pulses = max(1, int(math.ceil(dur / max(0.25, pulse_q) - 1e-4)))

        def pulse_ev(k: int) -> AudioEvent:
            p_on = onset + k * pulse_q
            rem = onset + dur - p_on
            p_dur = max(0.15, min(pulse_q * 0.92, rem))
            vel = 0.36 if k == 0 else 0.24
            return AudioEvent(p_on, p_dur, pad, vel)

        return (bass_ev, *map(pulse_ev, range(n_pulses)))

    return tuple(chain.from_iterable(map(expand_span, chords)))


_KARAOKE_CSS = """
:root {
  --bg: #08111e;
  --panel: #101d31;
  --panel-border: rgba(56, 189, 248, 0.22);
  --cyan: #22d3ee;
  --gold: #facc15;
  --gold-soft: rgba(250, 204, 21, 0.2);
  --green: #34d399;
  --text: #f1f5f9;
  --muted: #94a3b8;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: radial-gradient(circle at top, #13233d 0%, var(--bg) 65%);
  color: var(--text);
  min-height: 100vh;
}
.kt-shell { max-width: 1240px; margin: 0 auto; padding: 18px 20px 36px; display: flex; flex-direction: column; gap: 16px; }
.kt-header {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 14px;
  background: rgba(16, 29, 49, 0.92); border: 1px solid var(--panel-border); border-radius: 14px; padding: 14px 18px;
}
.kt-brand h1 { margin: 0; font-size: 1.35rem; letter-spacing: 0.01em; color: var(--cyan); }
.kt-sub { margin: 4px 0 0; font-size: 0.85rem; color: var(--muted); }
.kt-meta-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.kt-badge {
  background: rgba(34, 211, 238, 0.12); border: 1px solid rgba(34, 211, 238, 0.35);
  color: var(--cyan); border-radius: 999px; padding: 4px 11px; font-size: 0.8rem; font-weight: 600;
}
.kt-controls-top { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.kt-select, .kt-btn {
  border-radius: 9px; border: 1px solid var(--panel-border); background: #0d182a; color: var(--text);
  padding: 8px 13px; font-size: 0.88rem; cursor: pointer; font-weight: 600; transition: 0.15s ease;
}
.kt-btn:hover { border-color: var(--cyan); transform: translateY(-1px); }
.kt-btn-primary { background: linear-gradient(135deg, #0ea5e9, #22d3ee); color: #041322; border: none; }
.kt-btn-gold { background: linear-gradient(135deg, #eab308, #fde047); color: #1b1400; border: none; }
.kt-btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
.kt-file-lbl { display: inline-flex; align-items: center; gap: 6px; }
.kt-file-lbl input { display: none; }
.kt-mode-tabs { display: flex; flex-wrap: wrap; gap: 8px; }
.kt-mode-tab {
  background: #0d182a; border: 1px solid var(--panel-border); color: var(--muted);
  border-radius: 999px; padding: 6px 14px; font-size: 0.84rem; font-weight: 600; cursor: pointer;
}
.kt-mode-tab.active { background: var(--cyan); color: #051626; border-color: var(--cyan); }
.kt-stage {
  background: linear-gradient(160deg, #10203a 0%, #091323 100%);
  border: 2px solid rgba(250, 204, 21, 0.36); border-radius: 16px; padding: 18px 22px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
}
.kt-stage-top { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; }
.kt-now-pills { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.kt-pill-note {
  background: rgba(250, 204, 21, 0.16); border: 1px solid var(--gold); color: #fef08a;
  padding: 6px 14px; border-radius: 999px; font-size: 1rem; font-weight: 700; min-width: 195px;
}
.kt-pill-chord {
  background: rgba(52, 211, 153, 0.14); border: 1px solid var(--green); color: #a7f3d0;
  padding: 6px 13px; border-radius: 999px; font-size: 0.92rem; font-weight: 700;
}
.kt-beat-dots { display: flex; align-items: center; gap: 7px; }
.kt-beat-dot {
  width: 24px; height: 24px; border-radius: 50%; background: #172742; border: 1px solid #334a6e;
  display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; color: var(--muted); font-weight: 700;
}
.kt-beat-dot.lit { background: var(--cyan); color: #041322; border-color: #fff; box-shadow: 0 0 12px var(--cyan); }
.kt-beat-dot.countin { background: var(--gold); color: #1f1700; border-color: #fff; box-shadow: 0 0 14px var(--gold); }
.kt-lyric-current {
  font-size: 2.05rem; font-weight: 800; line-height: 1.45; min-height: 3.1rem;
  display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: baseline; padding: 6px 0;
}
.kt-lyric-next { font-size: 1.02rem; color: var(--muted); min-height: 1.5rem; margin-top: 4px; }
.karaoke-word {
  position: relative; display: inline-block; cursor: pointer; padding: 2px 6px; border-radius: 8px;
  color: #cbd5e1; transition: transform 0.1s ease, background 0.15s ease;
}
.karaoke-word:hover { background: rgba(255, 255, 255, 0.08); }
.karaoke-word.sung { color: var(--cyan); }
.karaoke-word.active {
  color: var(--gold);
  background: rgba(250, 204, 21, 0.16);
  box-shadow: 0 0 0 2px rgba(250, 204, 21, 0.55);
  transform: scale(1.06);
}
.karaoke-word-tag {
  font-size: 0.68rem; font-weight: 700; color: var(--muted); margin-right: 4px;
  vertical-align: middle; text-transform: uppercase; letter-spacing: 0.03em;
}
.karaoke-word.active .karaoke-word-tag { color: #fde047; }
.kt-staff-panel {
  background: var(--panel); border: 1px solid var(--panel-border); border-radius: 14px; padding: 14px 16px;
}
.kt-staff-viewport { display: flex; flex-direction: column; gap: 12px; max-height: 430px; overflow-y: auto; padding-right: 4px; }
.kt-phrase-card {
  background: #0a1425; border: 1px solid rgba(148, 163, 184, 0.18); border-radius: 10px; padding: 8px 10px 6px;
  overflow-x: auto; position: relative; transition: border-color 0.2s ease;
}
.kt-phrase-card.active-phrase { border-color: var(--gold); box-shadow: 0 0 0 1px rgba(250, 204, 21, 0.45); }
.kt-phrase-hdr { font-size: 0.76rem; font-weight: 700; color: var(--cyan); letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 2px; }
.kt-controls-card {
  background: var(--panel); border: 1px solid var(--panel-border); border-radius: 14px; padding: 16px 18px;
  display: flex; flex-direction: column; gap: 14px;
}
.kt-transport { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.kt-status { margin-left: auto; font-size: 0.88rem; color: var(--cyan); font-weight: 600; }
.kt-mixer-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px 18px; align-items: center; }
.kt-slider-box { display: flex; flex-direction: column; gap: 5px; font-size: 0.84rem; color: #e2e8f0; }
.kt-slider-box input[type="range"] { width: 100%; accent-color: var(--cyan); }
.kt-speed-presets { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 2px; }
.kt-preset {
  padding: 4px 10px; font-size: 0.78rem; font-weight: 700; border-radius: 7px;
  background: #0a1425; border: 1px solid var(--panel-border); color: var(--muted); cursor: pointer;
}
.kt-preset.active { background: var(--gold); color: #191300; border-color: var(--gold); }
.kt-kbd-wrap {
  background: var(--panel); border: 1px solid var(--panel-border); border-radius: 14px; padding: 12px 16px; overflow-x: auto;
}
.kt-kbd { position: relative; height: 96px; min-width: 864px; margin: 6px auto 0; }
.kt-wk {
  position: absolute; top: 0; width: 24px; height: 92px; background: #f8fafc; border: 1px solid #475569;
  border-radius: 0 0 4px 4px; color: #334155; font-size: 0.62rem; display: flex; align-items: flex-end; justify-content: center; padding-bottom: 3px;
}
.kt-bk {
  position: absolute; top: 0; width: 15px; height: 58px; background: #0f172a; border: 1px solid #334155;
  border-radius: 0 0 3px 3px; z-index: 2;
}
.kt-wk.melody-lit, .kt-bk.melody-lit { background: var(--gold) !important; color: #1b1400; box-shadow: 0 0 12px var(--gold); }
.kt-wk.chord-lit, .kt-bk.chord-lit { background: #38bdf8 !important; color: #051626; }
"""


_KARAOKE_JS = r"""
(() => {
  const API_MODE = Boolean(window.__KARAOKE_API_MODE__);
  let currentScore = window.__INITIAL_KARAOKE_DATA__ || null;
  let currentModeIndex = 0;
  let speedRatio = 1.0;
  let semitoneShift = 0;

  // Web Audio & scheduler state
  let audioCtx = null;
  let isPlaying = false;
  let isPaused = false;
  let songPosQ = 0;          // current beat position inside active mode
  let countInRemainingQ = 0; // remaining count-in beats before beat 0
  let nextNoteIdx = 0;
  let nextChordIdx = 0;
  let nextClickQ = 0;
  let nextCountClickQ = 0;
  let startClockTime = 0;
  let rafId = null;
  let schedulerTimer = null;
  let lastWallTime = 0;

  const $ = (id) => document.getElementById(id);
  const elScoreSelect = $('ktScoreSelect');
  const elPdfUpload = $('ktPdfUpload');
  const elTitle = $('ktTitle');
  const elSub = $('ktSub');
  const elKeyBadge = $('ktKeyBadge');
  const elTimeBadge = $('ktTimeBadge');
  const elTempoBadge = $('ktTempoBadge');
  const elModeTabs = $('ktModeTabs');
  const elNotePill = $('ktActiveNotePill');
  const elChordPill = $('ktActiveChordPill');
  const elBeatDots = $('ktBeatDots');
  const elCurrentLine = $('ktCurrentLine');
  const elNextLine = $('ktNextLine');
  const elStaffViewport = $('ktStaffViewport');
  const elPlayBtn = $('ktPlayBtn');
  const elPauseBtn = $('ktPauseBtn');
  const elStopBtn = $('ktStopBtn');
  const elLoopToggle = $('ktLoopToggle');
  const elCountInToggle = $('ktCountInToggle');
  const elStatus = $('ktStatus');
  const elVocalVol = $('ktVocalVol');
  const elBgVol = $('ktBgVol');
  const elClickVol = $('ktClickVol');
  const elVocalVal = $('ktVocalVal');
  const elBgVal = $('ktBgVal');
  const elClickVal = $('ktClickVal');
  const elBpmSlider = $('ktBpmSlider');
  const elBpmVal = $('ktBpmVal');
  const elSpeedVal = $('ktSpeedVal');
  const elTranspose = $('ktTranspose');
  const elKeyboard = $('ktKeyboard');
  const presetBtns = Array.from(document.querySelectorAll('.kt-preset'));

  function activeMode() {
    if (!currentScore || !currentScore.modes || !currentScore.modes.length) return null;
    return currentScore.modes[Math.min(currentModeIndex, currentScore.modes.length - 1)];
  }

  function parseTimeSig(tsStr) {
    const parts = String(tsStr || '4/4').split('/');
    return [Math.max(1, parseInt(parts[0], 10) || 4), Math.max(1, parseInt(parts[1], 10) || 4)];
  }

  function effectiveQpm() {
    const base = currentScore ? (Number(currentScore.tempo_qpm) || 90) : 90;
    return Math.max(12, base * speedRatio);
  }

  function qToSec(q) {
    return (q * 60.0) / effectiveQpm();
  }

  function secToQ(sec) {
    return (sec * effectiveQpm()) / 60.0;
  }

  function midiToFreq(m) {
    return 440.0 * Math.pow(2.0, (m - 69) / 12.0);
  }

  function midiToName(m) {
    const names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const oct = Math.floor(m / 12) - 1;
    return names[((m % 12) + 12) % 12] + oct;
  }

  function diatonicStepFromE4(midi) {
    // Map pitch class onto major diatonic scale letter offsets (relative to E4 = 30)
    const oct = Math.floor(midi / 12) - 1;
    const pc = ((midi % 12) + 12) % 12;
    const pcStep = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6][pc];
    return (oct * 7 + pcStep) - 30;
  }

  function ensureAudio() {
    if (!audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) audioCtx = new Ctx();
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume().catch(() => {});
    }
    return audioCtx;
  }

  function scheduleVocalTone(midi, when, durSec, gainVal) {
    if (!audioCtx || gainVal <= 0.01) return;
    const freq = midiToFreq(midi);
    const out = audioCtx.createGain();
    const osc1 = audioCtx.createOscillator();
    const osc2 = audioCtx.createOscillator();
    const filter = audioCtx.createBiquadFilter();
    osc1.type = 'triangle';
    osc2.type = 'sine';
    osc1.frequency.setValueAtTime(freq, when);
    osc2.frequency.setValueAtTime(freq * 2.0, when);
    const g2 = audioCtx.createGain();
    g2.gain.setValueAtTime(0.22, when);

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(Math.max(1400, freq * 4.5), when);

    const endT = when + Math.max(0.05, durSec);
    out.gain.setValueAtTime(0.0001, when);
    out.gain.exponentialRampToValueAtTime(0.32 * gainVal, when + Math.min(0.035, durSec * 0.25));
    out.gain.setValueAtTime(0.28 * gainVal, Math.max(when + 0.04, endT - 0.045));
    out.gain.exponentialRampToValueAtTime(0.0001, endT + 0.02);

    osc1.connect(filter);
    osc2.connect(g2);
    g2.connect(filter);
    filter.connect(out);
    out.connect(audioCtx.destination);
    osc1.start(when);
    osc2.start(when);
    osc1.stop(endT + 0.03);
    osc2.stop(endT + 0.03);
  }

  function scheduleChordPulse(bassMidi, chordMidis, when, durSec, gainVal, isDownbeat) {
    if (!audioCtx || gainVal <= 0.01) return;
    const endT = when + Math.max(0.08, durSec);
    if (isDownbeat && bassMidi) {
      const bo = audioCtx.createOscillator();
      const bg = audioCtx.createGain();
      bo.type = 'triangle';
      bo.frequency.setValueAtTime(midiToFreq(bassMidi), when);
      bg.gain.setValueAtTime(0.0001, when);
      bg.gain.exponentialRampToValueAtTime(0.18 * gainVal, when + 0.02);
      bg.gain.exponentialRampToValueAtTime(0.0001, endT + 0.05);
      bo.connect(bg);
      bg.connect(audioCtx.destination);
      bo.start(when);
      bo.stop(endT + 0.06);
    }
    const perNote = (isDownbeat ? 0.085 : 0.06) * gainVal;
    chordMidis.forEach((m) => {
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.type = 'sine';
      o.frequency.setValueAtTime(midiToFreq(m), when);
      g.gain.setValueAtTime(0.0001, when);
      g.gain.exponentialRampToValueAtTime(perNote, when + 0.025);
      g.gain.exponentialRampToValueAtTime(0.0001, endT);
      o.connect(g);
      g.connect(audioCtx.destination);
      o.start(when);
      o.stop(endT + 0.02);
    });
  }

  function scheduleClick(when, accent, gainVal) {
    if (!audioCtx || gainVal <= 0.01) return;
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.type = 'sine';
    o.frequency.setValueAtTime(accent ? 1320 : 880, when);
    g.gain.setValueAtTime(0.0001, when);
    g.gain.exponentialRampToValueAtTime((accent ? 0.28 : 0.17) * gainVal, when + 0.003);
    g.gain.exponentialRampToValueAtTime(0.0001, when + 0.055);
    o.connect(g);
    g.connect(audioCtx.destination);
    o.start(when);
    o.stop(when + 0.06);
  }

  // Build 61-key piano strip (MIDI 36..96)
  function buildKeyboard() {
    elKeyboard.innerHTML = '';
    const notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    let whiteIdx = 0;
    const wWidth = 24;
    for (let m = 36; m <= 96; m++) {
      const pc = m % 12;
      const oct = Math.floor(m / 12) - 1;
      const isBlack = notes[pc].includes('#');
      const k = document.createElement('div');
      k.setAttribute('data-midi', String(m));
      k.className = isBlack ? 'kt-bk' : 'kt-wk';
      if (isBlack) {
        k.style.left = `${(whiteIdx - 1) * wWidth + 16}px`;
      } else {
        k.style.left = `${whiteIdx * wWidth}px`;
        if (pc === 0) k.textContent = `C${oct}`;
        whiteIdx++;
      }
      k.addEventListener('mousedown', () => {
        ensureAudio();
        if (audioCtx) scheduleVocalTone(m + semitoneShift, audioCtx.currentTime, 0.55, 0.9);
      });
      elKeyboard.appendChild(k);
    }
  }

  function lightKeyboard(melMidi, chordMidis, bassMidi) {
    elKeyboard.querySelectorAll('.melody-lit, .chord-lit').forEach((el) => {
      el.classList.remove('melody-lit', 'chord-lit');
    });
    if (bassMidi !== null && bassMidi !== undefined) {
      const bEl = elKeyboard.querySelector(`[data-midi="${bassMidi + semitoneShift}"]`);
      if (bEl) bEl.classList.add('chord-lit');
    }
    (chordMidis || []).forEach((m) => {
      const cEl = elKeyboard.querySelector(`[data-midi="${m + semitoneShift}"]`);
      if (cEl) cEl.classList.add('chord-lit');
    });
    if (melMidi !== null && melMidi !== undefined) {
      const mEl = elKeyboard.querySelector(`[data-midi="${melMidi + semitoneShift}"]`);
      if (mEl) mEl.classList.add('melody-lit');
    }
  }

  function renderBeatDots() {
    const [tsNum] = parseTimeSig(currentScore ? currentScore.time_signature : '4/4');
    elBeatDots.innerHTML = '';
    for (let i = 0; i < tsNum; i++) {
      const dot = document.createElement('span');
      dot.className = 'kt-beat-dot';
      dot.textContent = String(i + 1);
      elBeatDots.appendChild(dot);
    }
  }

  function renderModeTabs() {
    elModeTabs.innerHTML = '';
    if (!currentScore || !currentScore.modes) return;
    currentScore.modes.forEach((m, idx) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'kt-mode-tab' + (idx === currentModeIndex ? ' active' : '');
      btn.setAttribute('data-testid', `mode-tab-${m.mode_id}`);
      btn.textContent = m.label;
      btn.addEventListener('click', () => {
        stopKaraoke();
        currentModeIndex = idx;
        renderModeTabs();
        renderStaffPhrases();
        updateVisualsAtQ(0, true);
      });
      elModeTabs.appendChild(btn);
    });
  }

  // Render Rule 2 & Rule 3 compliant 5-line SVG staff systems
  function renderStaffPhrases() {
    elStaffViewport.innerHTML = '';
    const mode = activeMode();
    if (!mode) return;

    const fifths = Number(currentScore.fifths || 0);
    const nKeyAcc = Math.min(7, Math.abs(fifths));
    const keyWidth = nKeyAcc * 11;
    const keyX = 50;
    const timeX = keyX + keyWidth + 8;
    const startBarX = timeX + 28;
    const firstNoteOffsetX = startBarX + 22;

    const sharpYs = [40, 58, 34, 52, 70, 46, 64]; // F5, C5, G5, D5, A4, E5, B4 (staff lines 40..88)
    const flatYs = [64, 46, 70, 52, 76, 58, 82];

    const phraseIndexToY = (midi) => 88 - diatonicStepFromE4(midi) * 6;

    mode.phrases.forEach((phrase, pIdx) => {
      const card = document.createElement('div');
      card.className = 'kt-phrase-card';
      card.setAttribute('data-phrase-index', String(pIdx));

      const hdr = document.createElement('div');
      hdr.className = 'kt-phrase-hdr';
      hdr.textContent = `${phrase.section_label} · Bars ${phrase.bar_start}-${phrase.bar_end}`;
      card.appendChild(hdr);

      const allEvs = [];
      phrase.bars.forEach((b) => b.events.forEach((e) => allEvs.push(e)));

      const stepW = Math.max(44, Math.min(62, 960 / Math.max(8, allEvs.length)));
      const svgWidth = Math.max(680, firstNoteOffsetX + allEvs.length * stepW + 40);
      const svgHeight = 148;

      let svgParts = [];
      svgParts.push(`<svg class="staff-svg" width="${svgWidth}" height="${svgHeight}" viewBox="0 0 ${svgWidth} ${svgHeight}">`);

      // 1. 5 horizontal staff lines (E4=88, G4=76, B4=64, D5=52, F5=40 -> 12px apart)
      for (let li = 0; li < 5; li++) {
        const yLine = 40 + li * 12;
        svgParts.push(`<line x1="0" y1="${yLine}" x2="${svgWidth}" y2="${yLine}" stroke="#475569" stroke-width="1.3"/>`);
      }

      // 2. Treble Clef centered on G4 (y=76) at x=10
      svgParts.push(`<text x="10" y="84" font-size="60" fill="#22d3ee" font-family="serif">&#x1D11E;</text>`);

      // 3. Key signature accidentals at x=50
      if (fifths > 0) {
        for (let k = 0; k < nKeyAcc; k++) {
          svgParts.push(`<text x="${keyX + k * 11}" y="${sharpYs[k] + 5}" font-size="18" fill="#cbd5e1">&#x266F;</text>`);
        }
      } else if (fifths < 0) {
        for (let k = 0; k < nKeyAcc; k++) {
          svgParts.push(`<text x="${keyX + k * 11}" y="${flatYs[k] + 5}" font-size="18" fill="#cbd5e1">&#x266D;</text>`);
        }
      }

      // 4. Stacked Time Signature
      const firstBar = phrase.bars[0] || { beats: 4, beat_type: 4 };
      svgParts.push(`<text x="${timeX + 8}" y="61" font-size="22" font-weight="800" text-anchor="middle" fill="#e2e8f0">${firstBar.beats}</text>`);
      svgParts.push(`<text x="${timeX + 8}" y="85" font-size="22" font-weight="800" text-anchor="middle" fill="#e2e8f0">${firstBar.beat_type}</text>`);

      // 5. Start measure barline
      svgParts.push(`<line x1="${startBarX}" y1="40" x2="${startBarX}" y2="88" stroke="#94a3b8" stroke-width="1.6"/>`);

      // 6. Compute X coordinate for every event & barlines
      const evCoords = [];
      let cursorIdx = 0;
      let prevChordShown = '';
      phrase.bars.forEach((b, bLocalIdx) => {
        b.events.forEach((e) => {
          const x = firstNoteOffsetX + cursorIdx * stepW + stepW * 0.45;
          evCoords.push({ ev: e, x });
          cursorIdx++;
        });
        const barLineX = firstNoteOffsetX + cursorIdx * stepW - 2;
        svgParts.push(`<line x1="${barLineX}" y1="40" x2="${barLineX}" y2="88" stroke="#64748b" stroke-width="${bLocalIdx === phrase.bars.length - 1 ? 2.2 : 1.2}"/>`);
      });

      // Beams on consecutive short notes (<= 0.5 quarter beats) inside each bar
      for (let i = 0; i < evCoords.length - 1; i++) {
        const c1 = evCoords[i];
        const c2 = evCoords[i + 1];
        if (
          c1.ev.kind === 'N' && c2.ev.kind === 'N' &&
          c1.ev.bar_number === c2.ev.bar_number &&
          c1.ev.dur_q <= 0.51 && c2.ev.dur_q <= 0.51
        ) {
          const y1 = phraseIndexToY(c1.ev.midi);
          const y2 = phraseIndexToY(c2.ev.midi);
          const sy1 = (y1 <= 64) ? (y1 + 26) : (y1 - 26);
          const sy2 = (y2 <= 64) ? (y2 + 26) : (y2 - 26);
          if ((y1 <= 64) === (y2 <= 64)) {
            svgParts.push(`<line x1="${c1.x + (y1 <= 64 ? -5 : 5)}" y1="${sy1}" x2="${c2.x + (y2 <= 64 ? -5 : 5)}" y2="${sy2}" stroke="#38bdf8" stroke-width="4.2" stroke-linecap="round"/>`);
          }
        }
      }

      // Noteheads, stems, ties, chords above, lyrics below
      evCoords.forEach((c, idx) => {
        const e = c.ev;
        const x = c.x;

        // Chord symbol above staff when changing
        if (e.chord_symbol && (idx === 0 || e.chord_symbol !== prevChordShown)) {
          svgParts.push(`<text x="${x}" y="20" font-size="13" font-weight="800" fill="#34d399" text-anchor="middle">${e.chord_symbol}</text>`);
          prevChordShown = e.chord_symbol;
        }

        if (e.kind === 'R') {
          const restGlyph = e.duration === 'whole' ? '&#x1D13B;' : e.duration === 'half' ? '&#x1D13C;' : e.duration === 'eighth' ? '&#x1D13E;' : '&#x1D13D;';
          const ry = e.duration === 'eighth' ? 74 : 72;
          svgParts.push(`<g class="staff-ev-group" data-ev-idx="${e.event_index}" data-onset-q="${e.onset_q}" style="cursor:pointer;">`);
          svgParts.push(`<text x="${x}" y="${ry}" font-size="28" fill="#64748b" text-anchor="middle">${restGlyph}</text>`);
          svgParts.push(`</g>`);
        } else {
          const y = phraseIndexToY(e.midi);
          const isHollow = e.duration === 'half' || e.duration === 'whole';
          svgParts.push(`<g class="staff-ev-group" data-ev-idx="${e.event_index}" data-onset-q="${e.onset_q}" data-midi="${e.midi}" style="cursor:pointer;">`);
          svgParts.push(`<rect x="${x - 14}" y="28" width="28" height="106" rx="6" fill="transparent" class="staff-ev-bg"/>`);

          // Ledger lines if needed
          if (y >= 100) {
            for (let ly = 100; ly <= y; ly += 12) {
              svgParts.push(`<line x1="${x - 10}" y1="${ly}" x2="${x + 10}" y2="${ly}" stroke="#94a3b8" stroke-width="1.4"/>`);
            }
          } else if (y <= 28) {
            for (let ly = 28; ly >= y; ly -= 12) {
              svgParts.push(`<line x1="${x - 10}" y1="${ly}" x2="${x + 10}" y2="${ly}" stroke="#94a3b8" stroke-width="1.4"/>`);
            }
          }

          // Stem direction (Rule 3.3: stems UP on right below B4 (y>64), DOWN on left on/above B4 (y<=64))
          if (e.duration !== 'whole') {
            if (y <= 64) {
              svgParts.push(`<line x1="${x - 5.2}" y1="${y}" x2="${x - 5.2}" y2="${y + 26}" stroke="#e2e8f0" stroke-width="1.8"/>`);
            } else {
              svgParts.push(`<line x1="${x + 5.2}" y1="${y}" x2="${x + 5.2}" y2="${y - 26}" stroke="#e2e8f0" stroke-width="1.8"/>`);
            }
          }

          // Notehead
          svgParts.push(
            `<ellipse cx="${x}" cy="${y}" rx="6.5" ry="4.6" transform="rotate(-18 ${x} ${y})" ` +
            `fill="${isHollow ? '#0a1425' : '#22d3ee'}" stroke="#22d3ee" stroke-width="2" class="staff-head" data-ev-idx="${e.event_index}"/>`
          );

          // Augmentation dot
          if (e.has_dot) {
            svgParts.push(`<circle cx="${x + 10.5}" cy="${y - 1}" r="2.1" fill="#e2e8f0"/>`);
          }

          // Tie arc to next event in phrase
          if (e.tie_start && idx + 1 < evCoords.length) {
            const nx = evCoords[idx + 1].x;
            svgParts.push(`<path d="M ${x + 3} ${y + 7} Q ${(x + nx) / 2} ${y + 18} ${nx - 3} ${y + 7}" fill="none" stroke="#38bdf8" stroke-width="2"/>`);
          }

          // Lyric syllable below staff
          if (e.lyric) {
            svgParts.push(`<text x="${x}" y="128" font-size="14" font-weight="700" fill="#f1f5f9" text-anchor="middle" class="staff-lyric" data-ev-idx="${e.event_index}">${e.lyric.replace(/</g, '&lt;')}</text>`);
          }
          svgParts.push(`</g>`);
        }
      });

      // Vertical glowing playhead line
      svgParts.push(`<line x1="-10" y1="22" x2="-10" y2="136" stroke="#facc15" stroke-width="2.4" stroke-dasharray="4 3" class="kt-playhead" opacity="0"/>`);
      svgParts.push(`</svg>`);

      const wrap = document.createElement('div');
      wrap.innerHTML = svgParts.join('');
      const svgEl = wrap.firstElementChild;
      card.appendChild(svgEl);

      // Attach click-to-jump / audition handlers
      svgEl.querySelectorAll('.staff-ev-group').forEach((g) => {
        const evIdx = parseInt(g.getAttribute('data-ev-idx'), 10);
        const onsetQ = parseFloat(g.getAttribute('data-onset-q'));
        const midi = parseInt(g.getAttribute('data-midi'), 10);
        const match = evCoords.find((item) => item.ev.event_index === evIdx);
        g.setAttribute('data-x', String(match ? match.x : firstNoteOffsetX));
        g.addEventListener('click', () => {
          ensureAudio();
          if (!Number.isNaN(midi) && audioCtx) {
            scheduleVocalTone(midi + semitoneShift, audioCtx.currentTime, 0.45, 0.9);
          }
          jumpToQ(onsetQ);
        });
      });

      elStaffViewport.appendChild(card);
    });
  }

  function renderPhraseTeleprompter(phrase, qPos) {
    const mode = activeMode();
    elCurrentLine.innerHTML = '';
    if (!phrase || !phrase.words.length) {
      elCurrentLine.innerHTML = '<span style="color:#94a3b8;font-size:1.2rem;">Instrumental / Rest measure...</span>';
    } else {
      phrase.words.forEach((w, idx) => {
        const span = document.createElement('span');
        const isActive = qPos >= w.start_q - 1e-4 && qPos < w.end_q - 1e-4;
        const isSung = qPos >= w.end_q - 1e-4;
        span.className = 'karaoke-word' + (isActive ? ' active' : (isSung ? ' sung' : ''));
        span.setAttribute('data-testid', `karaoke-word-${idx}`);
        const noteTag = document.createElement('span');
        noteTag.className = 'karaoke-word-tag';
        noteTag.textContent = w.pitch_name;
        span.appendChild(noteTag);
        span.appendChild(document.createTextNode(w.text));
        span.addEventListener('click', () => {
          ensureAudio();
          if (w.midi && audioCtx) scheduleVocalTone(w.midi + semitoneShift, audioCtx.currentTime, 0.45, 0.9);
          jumpToQ(w.start_q);
        });
        elCurrentLine.appendChild(span);
      });
    }

    const nextPhrase = mode && phrase ? mode.phrases[phrase.phrase_index + 1] : null;
    if (nextPhrase && nextPhrase.words.length) {
      const joined = nextPhrase.words.map((w) => w.text).join(' ').replace(/-\s+/g, '');
      elNextLine.textContent = `Next (${nextPhrase.section_label}): ${joined}`;
    } else {
      elNextLine.textContent = 'End of selection';
    }
  }

  function flattenEvents(mode) {
    const out = [];
    if (!mode) return out;
    mode.phrases.forEach((p) => p.bars.forEach((b) => b.events.forEach((e) => out.push(e))));
    return out;
  }

  function updateVisualsAtQ(qPos, forcePhraseRender = false) {
    const mode = activeMode();
    if (!mode || !mode.phrases.length) return;
    const allEvs = flattenEvents(mode);
    const activeEv = allEvs.find((e) => qPos >= e.onset_q - 1e-4 && qPos < e.onset_q + e.dur_q - 1e-4) || allEvs[0];
    const activeChord = mode.chords.find((c) => qPos >= c.onset_q - 1e-4 && qPos < c.end_q - 1e-4) || mode.chords[0];
    const activePhrase = mode.phrases.find((p) => qPos >= p.start_q - 1e-4 && qPos < p.end_q - 1e-4) || mode.phrases[0];

    // Update top cue pills right next to lyrics
    if (activeEv) {
      if (activeEv.kind === 'R') {
        elNotePill.textContent = '💨 Rest · Breathe';
      } else {
        const noteLbl = midiToName(activeEv.midi + semitoneShift);
        const wordCue = activeEv.active_word ? ` · "${activeEv.active_word}"` : '';
        elNotePill.textContent = `🎵 ${noteLbl}${wordCue}`;
      }
    }
    if (activeChord) {
      elChordPill.textContent = `🎹 Chord: ${activeChord.symbol}`;
    }

    // Light piano visualizer keys
    lightKeyboard(
      (activeEv && activeEv.kind === 'N') ? activeEv.midi : null,
      activeChord ? activeChord.chord_midis : [],
      activeChord ? activeChord.bass_midi : null,
    );

    // Beat dots
    const [tsNum, tsDen] = parseTimeSig(currentScore.time_signature);
    const stepQ = 4.0 / tsDen;
    const dots = Array.from(elBeatDots.children);
    dots.forEach((d) => d.classList.remove('lit', 'countin'));
    if (countInRemainingQ > 0.001) {
      const elapsedCiQ = (tsNum * stepQ) - countInRemainingQ;
      const dotIdx = Math.max(0, Math.min(tsNum - 1, Math.floor(elapsedCiQ / stepQ + 1e-5)));
      if (dots[dotIdx]) dots[dotIdx].classList.add('countin');
    } else if (isPlaying) {
      const curBar = mode.phrases
        .flatMap((p) => p.bars)
        .find((b) => qPos >= b.start_q - 1e-4 && qPos < b.start_q + b.dur_q - 1e-4);
      if (curBar) {
        const beatIdx = Math.max(0, Math.min(dots.length - 1, Math.floor((qPos - curBar.start_q) / stepQ + 1e-5)));
        if (dots[beatIdx]) dots[beatIdx].classList.add('lit');
      }
    }

    // Teleprompter words
    renderPhraseTeleprompter(activePhrase, qPos);

    // Staff note + syllable highlight & vertical playhead
    elStaffViewport.querySelectorAll('.kt-phrase-card').forEach((card) => {
      const isActPhrase = Number(card.getAttribute('data-phrase-index')) === activePhrase.phrase_index;
      card.classList.toggle('active-phrase', isActPhrase);
      const ph = card.querySelector('.kt-playhead');
      if (ph && !isActPhrase) ph.setAttribute('opacity', '0');
    });

    elStaffViewport.querySelectorAll('.staff-head').forEach((h) => {
      const isAct = activeEv && Number(h.getAttribute('data-ev-idx')) === activeEv.event_index;
      h.setAttribute('fill', isAct ? '#facc15' : '#22d3ee');
      h.setAttribute('stroke', isAct ? '#ffffff' : '#22d3ee');
    });
    elStaffViewport.querySelectorAll('.staff-lyric').forEach((t) => {
      const isAct = activeEv && Number(t.getAttribute('data-ev-idx')) === activeEv.event_index;
      t.setAttribute('fill', isAct ? '#facc15' : '#f1f5f9');
    });
    if (activeEv) {
      const activeGroup = elStaffViewport.querySelector(`.staff-ev-group[data-ev-idx="${activeEv.event_index}"]`);
      if (activeGroup) {
        const card = activeGroup.closest('.kt-phrase-card');
        const ph = card ? card.querySelector('.kt-playhead') : null;
        if (ph) {
          ph.setAttribute('x1', activeGroup.getAttribute('data-x') || '0');
          ph.setAttribute('x2', activeGroup.getAttribute('data-x') || '0');
          ph.setAttribute('opacity', '0.95');
        }
        if (forcePhraseRender || isPlaying) {
          card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }
    }
  }

  function resetCursorsAtQ(qPos) {
    const mode = activeMode();
    if (!mode) return;
    const allEvs = flattenEvents(mode);
    nextNoteIdx = allEvs.findIndex((e) => e.onset_q >= qPos - 1e-4);
    if (nextNoteIdx < 0) nextNoteIdx = allEvs.length;

    const [, tsDen] = parseTimeSig(currentScore.time_signature);
    const stepQ = 4.0 / tsDen;
    nextClickQ = Math.ceil((qPos - 1e-4) / stepQ) * stepQ;
    nextChordIdx = 0;
  }

  function jumpToQ(targetQ) {
    songPosQ = Math.max(0, targetQ);
    countInRemainingQ = 0;
    resetCursorsAtQ(songPosQ);
    if (isPlaying && !isPaused) {
      startClockTime = (audioCtx && audioCtx.state === 'running' ? audioCtx.currentTime : 0) - qToSec(songPosQ);
      lastWallTime = performance.now();
    }
    updateVisualsAtQ(songPosQ, true);
  }

  function runLookaheadScheduler() {
    if (!isPlaying || isPaused) return;
    const mode = activeMode();
    if (!mode) return;
    const allEvs = flattenEvents(mode);
    const vocalGain = Number(elVocalVol.value) / 100.0;
    const bgGain = Number(elBgVol.value) / 100.0;
    const clickGain = Number(elClickVol.value) / 100.0;
    const [tsNum, tsDen] = parseTimeSig(currentScore.time_signature);
    const stepQ = 4.0 / tsDen;
    const barQ = tsNum * stepQ;
    const nowA = audioCtx && audioCtx.state === 'running' ? audioCtx.currentTime : 0;

    if (audioCtx && audioCtx.state === 'running') {
      const songZeroAudio = startClockTime;
      const horizonSec = 0.16;

      // Count-in clicks
      while (countInRemainingQ > 0.001 && nextCountClickQ < barQ - 1e-4) {
        const clickTime = (songZeroAudio - qToSec(barQ)) + qToSec(nextCountClickQ);
        if (clickTime <= nowA + horizonSec) {
          scheduleClick(Math.max(nowA, clickTime), Math.round(nextCountClickQ / stepQ) % tsNum === 0, Math.max(0.45, clickGain));
          nextCountClickQ += stepQ;
        } else {
          break;
        }
      }

      // Melody vocal guide notes
      while (nextNoteIdx < allEvs.length) {
        const ev = allEvs[nextNoteIdx];
        const when = songZeroAudio + qToSec(ev.onset_q);
        if (when <= nowA + horizonSec) {
          if (ev.kind === 'N' && !ev.tie_stop) {
            scheduleVocalTone(ev.midi + semitoneShift, Math.max(nowA, when), qToSec(ev.sound_dur_q), vocalGain);
          }
          nextNoteIdx++;
        } else {
          break;
        }
      }

      // Background music harmonic accompaniment pulses
      const chordStepQ = (tsNum in { 6: 1, 9: 1, 12: 1 } && tsDen === 8) ? 1.5 : stepQ;
      while (nextChordIdx * chordStepQ < mode.total_beats_q - 1e-4) {
        const cq = nextChordIdx * chordStepQ;
        const when = songZeroAudio + qToSec(cq);
        if (when <= nowA + horizonSec) {
          const ch = mode.chords.find((c) => cq >= c.onset_q - 1e-4 && cq < c.end_q - 1e-4);
          if (ch) {
            const durQ = Math.min(chordStepQ * 0.94, ch.end_q - cq);
            const isDown = Math.abs(cq % barQ) < 1e-3 || Math.abs(cq - ch.onset_q) < 1e-3;
            scheduleChordPulse(
              ch.bass_midi + semitoneShift,
              ch.chord_midis.map((m) => m + semitoneShift),
              Math.max(nowA, when),
              qToSec(durQ),
              bgGain,
              isDown,
            );
          }
          nextChordIdx++;
        } else {
          break;
        }
      }

      // Beat clicks
      while (nextClickQ < mode.total_beats_q - 1e-4) {
        const when = songZeroAudio + qToSec(nextClickQ);
        if (when <= nowA + horizonSec) {
          const isBarStart = Math.round(nextClickQ / stepQ) % tsNum === 0;
          scheduleClick(Math.max(nowA, when), isBarStart, clickGain);
          nextClickQ += stepQ;
        } else {
          break;
        }
      }
    }
  }

  function animationTick() {
    if (!isPlaying || isPaused) return;
    const mode = activeMode();
    if (!mode) return;

    const nowWall = performance.now();
    const dtSec = Math.max(0, (nowWall - lastWallTime) / 1000.0);
    lastWallTime = nowWall;

    const dtQ = (audioCtx && audioCtx.state === 'running' && startClockTime > 0 && audioCtx.currentTime > startClockTime - 10)
      ? null
      : secToQ(dtSec);

    if (dtQ === null && audioCtx) {
      const relSec = audioCtx.currentTime - startClockTime;
      if (relSec < 0) {
        countInRemainingQ = secToQ(-relSec);
        songPosQ = 0;
      } else {
        countInRemainingQ = 0;
        songPosQ = secToQ(relSec);
      }
    } else if (countInRemainingQ > 0) {
      countInRemainingQ -= dtQ;
      if (countInRemainingQ <= 0) {
        songPosQ = -countInRemainingQ;
        countInRemainingQ = 0;
      }
    } else {
      songPosQ += dtQ;
    }

    if (songPosQ >= mode.total_beats_q) {
      if (elLoopToggle && elLoopToggle.checked) {
        songPosQ = 0;
        countInRemainingQ = 0;
        if (audioCtx && audioCtx.state === 'running') startClockTime = audioCtx.currentTime;
        resetCursorsAtQ(0);
      } else {
        stopKaraoke();
        elStatus.textContent = 'Finished!';
        return;
      }
    }

    updateVisualsAtQ(songPosQ, false);
    rafId = requestAnimationFrame(animationTick);
  }

  function startKaraoke() {
    const mode = activeMode();
    if (!mode) return;
    ensureAudio();
    const [tsNum, tsDen] = parseTimeSig(currentScore.time_signature);
    const barQ = tsNum * (4.0 / tsDen);
    const useCi = !isPaused && songPosQ < 1e-4 && elCountInToggle && elCountInToggle.checked;

    isPlaying = true;
    isPaused = false;
    elPlayBtn.disabled = true;
    elPauseBtn.disabled = false;
    elStopBtn.disabled = false;

    if (useCi) {
      countInRemainingQ = barQ;
      nextCountClickQ = 0;
      elStatus.textContent = 'Count-In...';
    } else {
      countInRemainingQ = 0;
      elStatus.textContent = 'Playing Karaoke';
    }

    resetCursorsAtQ(songPosQ);
    lastWallTime = performance.now();
    if (audioCtx) {
      const ciSec = qToSec(countInRemainingQ);
      startClockTime = audioCtx.currentTime + ciSec - qToSec(songPosQ);
    }

    clearInterval(schedulerTimer);
    schedulerTimer = setInterval(runLookaheadScheduler, 45);
    runLookaheadScheduler();
    cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(animationTick);
  }

  function pauseKaraoke() {
    isPlaying = false;
    isPaused = true;
    clearInterval(schedulerTimer);
    cancelAnimationFrame(rafId);
    elPlayBtn.disabled = false;
    elPauseBtn.disabled = true;
    elStatus.textContent = 'Paused';
  }

  function stopKaraoke() {
    isPlaying = false;
    isPaused = false;
    songPosQ = 0;
    countInRemainingQ = 0;
    clearInterval(schedulerTimer);
    cancelAnimationFrame(rafId);
    elPlayBtn.disabled = false;
    elPauseBtn.disabled = true;
    elStopBtn.disabled = true;
    elStatus.textContent = 'Ready';
    updateVisualsAtQ(0, true);
  }

  function loadScoreObject(data) {
    stopKaraoke();
    currentScore = data;
    currentModeIndex = 0;
    speedRatio = 1.0;

    elTitle.textContent = `🎤 ${data.title || 'Karaoke Trainer'}`;
    elSub.textContent = data.composer ? `${data.composer} — Live Note, Word & Chord Trainer` : 'Live Note, Word & Chord Trainer';
    elKeyBadge.textContent = `Key: ${data.key || 'C Major'}`;
    elTimeBadge.textContent = `Time: ${data.time_signature || '4/4'}`;
    const qpm = Math.round(Number(data.tempo_qpm || 90));
    elTempoBadge.textContent = `BPM: ${qpm}`;
    elBpmSlider.value = String(Math.max(15, Math.min(180, qpm)));
    elBpmVal.textContent = String(qpm);
    elSpeedVal.textContent = '100%';
    presetBtns.forEach((b) => b.classList.toggle('active', Math.abs(parseFloat(b.dataset.speed) - 1.0) < 0.01));

    renderBeatDots();
    renderModeTabs();
    renderStaffPhrases();
    updateVisualsAtQ(0, true);
  }

  function applySpeedRatio(r) {
    speedRatio = Math.max(0.15, Math.min(2.0, r));
    const effBpm = Math.round(effectiveQpm());
    elBpmSlider.value = String(Math.max(15, Math.min(180, effBpm)));
    elBpmVal.textContent = String(effBpm);
    elSpeedVal.textContent = `${Math.round(speedRatio * 100)}%`;
    elTempoBadge.textContent = `BPM: ${effBpm}`;
    presetBtns.forEach((b) => b.classList.toggle('active', Math.abs(parseFloat(b.dataset.speed) - speedRatio) < 0.02));
    if (isPlaying && audioCtx) {
      startClockTime = audioCtx.currentTime - qToSec(songPosQ);
    }
  }

  // Event bindings
  elPlayBtn.addEventListener('click', startKaraoke);
  elPauseBtn.addEventListener('click', pauseKaraoke);
  elStopBtn.addEventListener('click', stopKaraoke);

  presetBtns.forEach((btn) => {
    btn.addEventListener('click', () => applySpeedRatio(parseFloat(btn.dataset.speed)));
  });

  elBpmSlider.addEventListener('input', () => {
    const base = currentScore ? (Number(currentScore.tempo_qpm) || 90) : 90;
    const chosen = parseInt(elBpmSlider.value, 10) || base;
    applySpeedRatio(chosen / base);
  });

  elVocalVol.addEventListener('input', () => { elVocalVal.textContent = `${elVocalVol.value}%`; });
  elBgVol.addEventListener('input', () => { elBgVal.textContent = `${elBgVol.value}%`; });
  elClickVol.addEventListener('input', () => { elClickVal.textContent = `${elClickVol.value}%`; });
  elTranspose.addEventListener('change', () => {
    semitoneShift = parseInt(elTranspose.value, 10) || 0;
    updateVisualsAtQ(songPosQ, false);
  });

  if (API_MODE && elScoreSelect) {
    fetch('/api/karaoke/list')
      .then((r) => r.json())
      .then((payload) => {
        elScoreSelect.innerHTML = '';
        (payload.scores || []).forEach((s) => {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.textContent = s.label;
          elScoreSelect.appendChild(opt);
        });
        if (payload.scores && payload.scores.length) {
          return fetch(`/api/karaoke/score/${encodeURIComponent(payload.scores[0].id)}`)
            .then((r) => r.json())
            .then(loadScoreObject);
        }
      })
      .catch(() => { elStatus.textContent = 'Error loading list'; });

    elScoreSelect.addEventListener('change', () => {
      if (!elScoreSelect.value) return;
      fetch(`/api/karaoke/score/${encodeURIComponent(elScoreSelect.value)}`)
        .then((r) => r.json())
        .then(loadScoreObject);
    });
  }

  if (API_MODE && elPdfUpload) {
    elPdfUpload.addEventListener('change', (ev) => {
      const file = ev.target.files[0];
      if (!file) return;
      const fd = new FormData();
      fd.append('pdf', file);
      elStatus.textContent = 'Extracting chords & words from PDF...';
      fetch('/api/karaoke/upload', { method: 'POST', body: fd })
        .then((r) => r.json())
        .then((d) => {
          if (d && d.modes) {
            loadScoreObject(d);
            elStatus.textContent = 'Uploaded & ready';
          }
        });
    });
  }

  buildKeyboard();
  if (currentScore) {
    loadScoreObject(currentScore);
  }
})();
"""


def render_standalone_karaoke_html(
    karaoke_data: dict[str, Any] | None = None,
    api_mode: bool = False,
) -> str:
    """Render a self-contained HTML5 Karaoke Note + Word + Background Music Trainer."""
    title_text = html_escape(str((karaoke_data or {}).get("title", "Psalm Karaoke Trainer")))
    init_json = json.dumps(karaoke_data) if karaoke_data is not None else "null"
    api_flag = "true" if api_mode else "false"

    picker_html = (
        '<select id="ktScoreSelect" data-testid="karaoke-score-select" class="kt-select">'
        '<option value="">Loading Scores...</option></select>'
        '<label class="kt-btn kt-file-lbl" data-testid="karaoke-upload-label">'
        '<span>📄 Upload PDF</span>'
        '<input type="file" id="ktPdfUpload" accept=".pdf">'
        '</label>'
        '<a href="/" class="kt-btn" style="text-decoration:none;">🎹 Main Player</a>'
        if api_mode
        else ""
    )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"<title>Karaoke Trainer — {title_text}</title>\n"
        f"<style>{_KARAOKE_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="kt-shell">\n'
        '  <header class="kt-header">\n'
        '    <div class="kt-brand">\n'
        f'      <h1 id="ktTitle" data-testid="karaoke-title">🎤 {title_text}</h1>\n'
        '      <p id="ktSub" class="kt-sub">Live Note, Word &amp; Background Chord Trainer</p>\n'
        "    </div>\n"
        '    <div class="kt-meta-row">\n'
        '      <span id="ktKeyBadge" class="kt-badge">Key: --</span>\n'
        '      <span id="ktTimeBadge" class="kt-badge">Time: --</span>\n'
        '      <span id="ktTempoBadge" class="kt-badge">BPM: --</span>\n'
        "    </div>\n"
        f'    <div class="kt-controls-top">{picker_html}</div>\n'
        "  </header>\n"
        '  <div id="ktModeTabs" class="kt-mode-tabs" data-testid="karaoke-mode-tabs"></div>\n'
        '  <section class="kt-stage" data-testid="karaoke-stage">\n'
        '    <div class="kt-stage-top">\n'
        '      <div class="kt-now-pills">\n'
        '        <div id="ktActiveNotePill" data-testid="active-note-pill" class="kt-pill-note">🎵 Ready</div>\n'
        '        <div id="ktActiveChordPill" data-testid="active-chord-pill" class="kt-pill-chord">🎹 Chord: --</div>\n'
        "      </div>\n"
        '      <div id="ktBeatDots" data-testid="karaoke-beat-dots" class="kt-beat-dots"></div>\n'
        "    </div>\n"
        '    <div id="ktCurrentLine" data-testid="karaoke-current-line" class="kt-lyric-current"></div>\n'
        '    <div id="ktNextLine" data-testid="karaoke-next-line" class="kt-lyric-next"></div>\n'
        "  </section>\n"
        '  <section class="kt-staff-panel">\n'
        '    <div id="ktStaffViewport" data-testid="karaoke-staff-viewport" class="kt-staff-viewport"></div>\n'
        "  </section>\n"
        '  <section class="kt-controls-card">\n'
        '    <div class="kt-transport">\n'
        '      <button type="button" id="ktPlayBtn" data-testid="karaoke-play-btn" class="kt-btn kt-btn-gold">▶ Play Karaoke</button>\n'
        '      <button type="button" id="ktPauseBtn" data-testid="karaoke-pause-btn" class="kt-btn" disabled>⏸ Pause</button>\n'
        '      <button type="button" id="ktStopBtn" data-testid="karaoke-stop-btn" class="kt-btn" disabled>⏹ Stop</button>\n'
        '      <label class="kt-btn" style="display:inline-flex;align-items:center;gap:6px;">'
        '<input type="checkbox" id="ktCountInToggle" data-testid="countin-toggle" checked> Count-In</label>\n'
        '      <label class="kt-btn" style="display:inline-flex;align-items:center;gap:6px;">'
        '<input type="checkbox" id="ktLoopToggle" data-testid="loop-toggle"> 🔁 Loop</label>\n'
        '      <div id="ktStatus" data-testid="karaoke-status" class="kt-status">Ready</div>\n'
        "    </div>\n"
        '    <div class="kt-mixer-grid">\n'
        '      <div class="kt-slider-box">\n'
        '        <span>🎤 Vocal Guide: <strong id="ktVocalVal">85%</strong></span>\n'
        '        <input type="range" id="ktVocalVol" data-testid="vocal-vol-slider" min="0" max="100" value="85">\n'
        "      </div>\n"
        '      <div class="kt-slider-box">\n'
        '        <span>🎹 Background Music: <strong id="ktBgVal">70%</strong></span>\n'
        '        <input type="range" id="ktBgVol" data-testid="bg-vol-slider" min="0" max="100" value="70">\n'
        "      </div>\n"
        '      <div class="kt-slider-box">\n'
        '        <span>🥁 Beat Click: <strong id="ktClickVal">35%</strong></span>\n'
        '        <input type="range" id="ktClickVol" data-testid="click-vol-slider" min="0" max="100" value="35">\n'
        '      </div>\n'
        '      <div class="kt-slider-box">\n'
        '        <span>⏱ Speed: <strong id="ktBpmVal">72</strong> BPM (<strong id="ktSpeedVal">100%</strong>)</span>\n'
        '        <input type="range" id="ktBpmSlider" data-testid="karaoke-bpm-slider" min="15" max="180" value="72">\n'
        '        <div class="kt-speed-presets">\n'
        '          <button type="button" class="kt-preset active" data-speed="1.0" data-testid="karaoke-speed-100">100%</button>\n'
        '          <button type="button" class="kt-preset" data-speed="0.75" data-testid="karaoke-speed-75">75%</button>\n'
        '          <button type="button" class="kt-preset" data-speed="0.5" data-testid="karaoke-speed-50">50%</button>\n'
        '          <button type="button" class="kt-preset" data-speed="0.3333" data-testid="karaoke-speed-33">33%</button>\n'
        '          <button type="button" class="kt-preset" data-speed="0.25" data-testid="karaoke-speed-25">25%</button>\n'
        "        </div>\n"
        "      </div>\n"
        '      <div class="kt-slider-box">\n'
        '        <span>🎼 Vocal Transpose</span>\n'
        '        <select id="ktTranspose" class="kt-select">\n'
        '          <option value="-4">-4 Semitones</option><option value="-3">-3 Semitones</option>'
        '<option value="-2">-2 Semitones</option><option value="-1">-1 Semitone</option>'
        '<option value="0" selected>Original Key</option>'
        '<option value="1">+1 Semitone</option><option value="2">+2 Semitones</option>'
        '<option value="3">+3 Semitones</option><option value="4">+4 Semitones</option>\n'
        "        </select>\n"
        "      </div>\n"
        "    </div>\n"
        "  </section>\n"
        '  <section class="kt-kbd-wrap">\n'
        '    <div style="font-size:0.82rem;color:#94a3b8;font-weight:700;">Piano Pitch &amp; Backing Harmony Visualizer (Gold = Sung Note, Blue = Chord)</div>\n'
        '    <div id="ktKeyboard" data-testid="karaoke-keyboard" class="kt-kbd"></div>\n'
        "  </section>\n"
        "</div>\n"
        "<script>\n"
        f"window.__KARAOKE_API_MODE__ = {api_flag};\n"
        f"window.__INITIAL_KARAOKE_DATA__ = {init_json};\n"
        f"{_KARAOKE_JS}\n"
        "</script>\n"
        "<!-- APAF Bioinformatics | karaoke_trainer.py | Approved | 2026-11-15 -->\n"
        "</body>\n"
        "</html>\n"
    )


def export_karaoke_html(input_path: Path, out_html: Path) -> tuple[Path, dict[str, Any]]:
    """Build a standalone HTML5 Karaoke Trainer file from a vector PDF or psalm JSON."""
    input_path = Path(input_path)
    out_html = Path(out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    if input_path.suffix.lower() == ".json":
        data = extract_karaoke_from_psalm_dict(json.loads(input_path.read_text(encoding="utf-8")))
    else:
        data = extract_karaoke_score_from_pdf(input_path)
    html = render_standalone_karaoke_html(data, api_mode=False)
    out_html.write_text(html, encoding="utf-8")
    return out_html, data


# <!-- APAF Bioinformatics | karaoke_trainer.py | Approved | 2026-11-15 -->
