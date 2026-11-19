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
from functools import reduce
from itertools import chain
from pathlib import Path
from typing import Any, Sequence

import pdfplumber

from sheet_music_reader.export import lean_bridge
from sheet_music_reader.export import score_formatter
from sheet_music_reader.omr import vector_omr
from sheet_music_reader.export.audio_synth import AudioEvent

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


def load_karaoke_data(input_path: Path) -> dict[str, Any]:
    """Read a psalm JSON or a vector PDF and return the karaoke timeline."""
    input_path = Path(input_path)
    if input_path.suffix.lower() == ".json":
        return extract_karaoke_from_psalm_dict(json.loads(input_path.read_text(encoding="utf-8")))
    return extract_karaoke_score_from_pdf(input_path)


def export_karaoke_html(input_path: Path, out_html: Path) -> tuple[Path, dict[str, Any]]:
    """Write the offline single-file Karaoke Trainer for a vector PDF or psalm JSON."""
    from sheet_music_reader.karaoke import render

    data = load_karaoke_data(input_path)
    return render.write_standalone(data, Path(out_html)), data


# <!-- APAF Bioinformatics | extract.py | Approved | 2026-11-19 -->
