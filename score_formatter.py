"""Score exporters for MusicXML 3.1, GNU LilyPond 2.26, Standard MIDI, and Sing-Along WAV.

All functions preserve backward-compatible defaults (`speed=1.0`, `augment=1`) and use
functional composition / NumPy vectorization with zero imperative Python loops.
"""

from __future__ import annotations

import io
import re
import struct
from collections import deque
from fractions import Fraction
from functools import reduce
from itertools import chain
from typing import Any, Dict, Sequence, Tuple
from xml.sax.saxutils import escape as xml_escape

from audio_synth import AudioEvent, render_wav_bytes
from lean_bridge import (
    LeanBar,
    LeanEvent,
    TICKS_PER_QUARTER,
    TICKS_PER_WHOLE,
    _note_beats_from_dict,
    expected_bar_ticks,
    note_name_to_midi,
    quarters_to_ticks,
)

try:
    import mido
    from mido import Message, MidiFile, MidiTrack

    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False


KEY_TO_FIFTHS: Dict[str, int] = {
    "C Major": 0, "A Minor": 0, "0": 0,
    "G Major": 1, "E Minor": 1, "1#": 1,
    "D Major": 2, "B Minor": 2, "2#": 2,
    "A Major": 3, "F# Minor": 3, "3#": 3,
    "E Major": 4, "C# Minor": 4, "4#": 4,
    "B Major": 5, "G# Minor": 5, "5#": 5,
    "F# Major": 6, "D# Minor": 6, "6#": 6,
    "C# Major": 7, "A# Minor": 7, "7#": 7,
    "F Major": -1, "D Minor": -1, "1b": -1,
    "Bb Major": -2, "G Minor": -2, "2b": -2,
    "Eb Major": -3, "C Minor": -3, "3b": -3,
    "Ab Major": -4, "F Minor": -4, "4b": -4,
    "Db Major": -5, "Bb Minor": -5, "5b": -5,
    "Gb Major": -6, "Eb Minor": -6, "6b": -6,
    "Cb Major": -7, "Ab Minor": -7, "7b": -7,
}

FIFTHS_TO_LY_KEY: Dict[int, str] = {
    0: "c", 1: "g", 2: "d", 3: "a", 4: "e", 5: "b", 6: "fis", 7: "cis",
    -1: "f", -2: "bes", -3: "es", -4: "as", -5: "des", -6: "ges", -7: "ces",
}

_MIDI_SHARP_PC = ("c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b")
_MIDI_FLAT_PC = ("c", "des", "d", "ees", "e", "f", "ges", "g", "aes", "a", "bes", "b")

_TICKS_TO_XML_TYPE = {
    384: ("breve", False),
    192: ("whole", False),
    144: ("half", True),
    96: ("half", False),
    72: ("quarter", True),
    48: ("quarter", False),
    36: ("eighth", True),
    24: ("eighth", False),
    18: ("16th", True),
    12: ("16th", False),
    6: ("32nd", False),
}

_TICKS_TO_LY_DUR = {
    384: "\\breve",
    288: "1.",
    192: "1",
    144: "2.",
    168: "2..",
    96: "2",
    72: "4.",
    84: "4..",
    48: "4",
    36: "8.",
    42: "8..",
    24: "8",
    18: "16.",
    12: "16",
    6: "32",
}


def _fifths_from_psalm(psalm_data: Dict[str, Any]) -> int:
    key_str = str(psalm_data.get("key") or "").strip()
    sig_str = str(psalm_data.get("key_signature") or "").strip()
    if sig_str in KEY_TO_FIFTHS:
        return KEY_TO_FIFTHS[sig_str]
    if key_str in KEY_TO_FIFTHS:
        return KEY_TO_FIFTHS[key_str]
    return 0


def _effective_tempo(psalm_data: Dict[str, Any], speed: float = 1.0) -> float:
    base = float(psalm_data.get("tempo", 90) or 90)
    return max(5.0, base * max(0.05, float(speed)))


def _parse_pitch_parts(pitch_str: str, fallback_midi: int) -> Tuple[str, int, int]:
    """Return `(step, alter, octave)` from pitch string or fallback MIDI number."""
    m = re.match(r"^([A-Ga-g])([#♯b♭]*)(-?\d+)$", (pitch_str or "").strip())
    if m:
        step = m.group(1).upper()
        accs = m.group(2).replace("♯", "#").replace("♭", "b")
        alter = accs.count("#") - accs.count("b")
        octv = int(m.group(3))
        return step, alter, octv
    pc_names = (
        ("C", 0), ("C", 1), ("D", 0), ("E", -1), ("E", 0), ("F", 0),
        ("F", 1), ("G", 0), ("G", 1), ("A", 0), ("B", -1), ("B", 0),
    )
    step, alter = pc_names[int(fallback_midi) % 12]
    octv = (int(fallback_midi) // 12) - 1
    return step, alter, octv


def _ticks_to_xml_type(ticks: int) -> Tuple[str, bool]:
    if ticks in _TICKS_TO_XML_TYPE:
        return _TICKS_TO_XML_TYPE[ticks]
    if ticks >= 144:
        return ("whole", False)
    if ticks >= 72:
        return ("half", False)
    if ticks >= 36:
        return ("quarter", False)
    if ticks >= 18:
        return ("eighth", False)
    return ("16th", False)


def _ticks_to_ly_dur(ticks: int) -> str:
    if ticks in _TICKS_TO_LY_DUR:
        return _TICKS_TO_LY_DUR[ticks]
    frac = Fraction(max(1, int(ticks)), TICKS_PER_QUARTER)
    if frac.denominator == 1:
        return f"4*{frac.numerator}"
    return f"4*{frac.numerator}/{frac.denominator}"


def _midi_to_ly_pitch(midi: int, fifths: int = 0) -> str:
    pc_table = _MIDI_FLAT_PC if fifths < 0 else _MIDI_SHARP_PC
    name = pc_table[int(midi) % 12]
    octv = (int(midi) // 12) - 1
    marks = "'" * (octv - 3) if octv > 3 else "," * (3 - octv)
    return f"{name}{marks}"


def _build_rich_bars(
    psalm_data: Dict[str, Any],
    speed: float = 1.0,
    augment: int = 1,
    pad_incomplete_bars: bool = True,
) -> Tuple[Tuple[LeanBar, Tuple[str, ...]], ...]:
    """Convert `psalm_data` into bar-aligned LeanBars paired with per-event lyric strings."""
    aug_k = max(1, int(augment))
    ts_parts = str(psalm_data.get("time_signature", "4/4")).split("/")
    beats = (max(1, int(ts_parts[0])) if ts_parts and ts_parts[0].isdigit() else 4) * aug_k
    beat_type = max(1, int(ts_parts[1])) if len(ts_parts) > 1 and ts_parts[1].isdigit() else 4
    cap = expected_bar_ticks(beats, beat_type)
    raw_notes = psalm_data.get("response", {}).get("notes", [])

    def to_event_pair(n: Dict[str, Any]) -> Tuple[LeanEvent, str]:
        dur_q = _note_beats_from_dict(n) * aug_k
        ticks = max(1, quarters_to_ticks(dur_q))
        is_rest = (
            bool(n.get("rest"))
            or bool(n.get("is_rest"))
            or str(n.get("pitch", "")).upper() == "REST"
            or (n.get("midi") is None and not n.get("chord_midis"))
        )
        lyric = str(n.get("lyric") or "")
        if is_rest:
            return LeanEvent("R", ticks, False, False, ()), lyric
        if n.get("chord_midis"):
            pitches = tuple(sorted(set(map(int, n["chord_midis"]))))
        elif n.get("midi") is not None:
            pitches = (int(n["midi"]),)
        else:
            pitches = (note_name_to_midi(str(n.get("pitch", "C4"))),)
        tie_raw = str(n.get("tie") or "").lower()
        ev = LeanEvent(
            "N",
            ticks,
            tie_start=(tie_raw in ("start", "both", "continue", "true", "1") or n.get("tie") is True),
            tie_stop=(tie_raw in ("stop", "both", "continue")),
            pitches=pitches,
        )
        return ev, lyric

    raw_pairs = tuple(map(to_event_pair, raw_notes))

    def mark_pair_tie(
        acc: Tuple[list[Tuple[LeanEvent, str]], LeanEvent | None],
        pair: Tuple[LeanEvent, str],
    ) -> Tuple[list[Tuple[LeanEvent, str]], LeanEvent | None]:
        out, prev = acc
        ev, lyr = pair
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
        upd = LeanEvent(ev.kind, ev.ticks, ev.tie_start, stop, ev.pitches)
        return [*out, (upd, lyr)], upd

    tied_pairs, _ = reduce(mark_pair_tie, raw_pairs, ([], None))

    def chunk_step(
        acc: Tuple[list[Tuple[LeanBar, Tuple[str, ...]]], list[Tuple[LeanEvent, str]], int, int],
        pair: Tuple[LeanEvent, str],
    ) -> Tuple[list[Tuple[LeanBar, Tuple[str, ...]]], list[Tuple[LeanEvent, str]], int, int]:
        done, cur, cur_t, bar_idx = acc
        ev, lyr = pair
        next_t = cur_t + ev.ticks
        if next_t == cap:
            cur_all = [*cur, (ev, lyr)]
            bar = LeanBar(bar_idx, beats, beat_type, cap, tuple(map(lambda p: p[0], cur_all)))
            lyrs = tuple(map(lambda p: p[1], cur_all))
            return [*done, (bar, lyrs)], [], 0, bar_idx + 1
        if next_t > cap and cur_t > 0:
            head_t = cap - cur_t
            tail_t = ev.ticks - head_t
            head_ev = LeanEvent(ev.kind, head_t, ev.kind == "N", ev.tie_stop, ev.pitches)
            tail_ev = LeanEvent(ev.kind, tail_t, ev.tie_start, ev.kind == "N", ev.pitches)
            cur_all = [*cur, (head_ev, lyr)]
            bar = LeanBar(bar_idx, beats, beat_type, cap, tuple(map(lambda p: p[0], cur_all)))
            lyrs = tuple(map(lambda p: p[1], cur_all))
            return chunk_step(([*done, (bar, lyrs)], [], 0, bar_idx + 1), (tail_ev, ""))
        return done, [*cur, (ev, lyr)], next_t, bar_idx

    done, cur, cur_t, bar_idx = reduce(chunk_step, tied_pairs, ([], [], 0, 1))
    if cur:
        final_pairs = tuple(cur)
        if pad_incomplete_bars and cur_t < cap:
            final_pairs = (*final_pairs, (LeanEvent("R", cap - cur_t, False, False, ()), ""))
        bar = LeanBar(bar_idx, beats, beat_type, cap, tuple(map(lambda p: p[0], final_pairs)))
        lyrs = tuple(map(lambda p: p[1], final_pairs))
        done = [*done, (bar, lyrs)]
    return tuple(done)


def export_musicxml(
    psalm_data: Dict[str, Any],
    speed: float = 1.0,
    augment: int = 1,
    pad_incomplete_bars: bool = True,
) -> str:
    """Generate MusicXML 3.1 with exact integer divisions (48/quarter), key fifths, ties, rests, and tempo."""
    title = xml_escape(str(psalm_data.get("title", "Psalm")))
    composer = xml_escape(str(psalm_data.get("composer", "Traditional")))
    fifths = _fifths_from_psalm(psalm_data)
    eff_tempo = _effective_tempo(psalm_data, speed=speed)
    bpm_attr = f"{eff_tempo:.2f}".rstrip("0").rstrip(".")
    bars_with_lyrics = _build_rich_bars(
        psalm_data, speed=speed, augment=augment, pad_incomplete_bars=pad_incomplete_bars
    )

    if not bars_with_lyrics:
        ts_parts = str(psalm_data.get("time_signature", "4/4")).split("/")
        beats = ts_parts[0] if ts_parts else "4"
        beat_type = ts_parts[1] if len(ts_parts) > 1 else "4"
        bars_with_lyrics = (
            (LeanBar(1, int(beats), int(beat_type), expected_bar_ticks(int(beats), int(beat_type)), ()), ()),
        )

    def render_pitch_note(midi: int, ticks: int, is_chord: bool, ev: LeanEvent, lyric: str) -> Tuple[str, ...]:
        step, alter, octv = _parse_pitch_parts("", midi)
        note_type, has_dot = _ticks_to_xml_type(ticks)
        tie_tags = (
            *(('<tie type="stop"/>',) if ev.tie_stop else ()),
            *(('<tie type="start"/>',) if ev.tie_start else ()),
        )
        notations = (
            *(('<tied type="stop"/>',) if ev.tie_stop else ()),
            *(('<tied type="start"/>',) if ev.tie_start else ()),
        )
        return (
            "      <note>",
            *(("        <chord/>",) if is_chord else ()),
            "        <pitch>",
            f"          <step>{step}</step>",
            *((f"          <alter>{alter}</alter>",) if alter != 0 else ()),
            f"          <octave>{octv}</octave>",
            "        </pitch>",
            f"        <duration>{ticks}</duration>",
            *map(lambda t: f"        {t}", tie_tags),
            "        <voice>1</voice>",
            f"        <type>{note_type}</type>",
            *(("        <dot/>",) if has_dot else ()),
            *(("        <notations>", *map(lambda t: f"          {t}", notations), "        </notations>") if notations else ()),
            *((f"        <lyric><text>{xml_escape(lyric)}</text></lyric>",) if lyric and not is_chord else ()),
            "      </note>",
        )

    def render_event(ev_lyr: Tuple[LeanEvent, str]) -> Tuple[str, ...]:
        ev, lyr = ev_lyr
        if ev.kind == "R" or not ev.pitches:
            note_type, has_dot = _ticks_to_xml_type(ev.ticks)
            return (
                "      <note>",
                "        <rest/>",
                f"        <duration>{ev.ticks}</duration>",
                "        <voice>1</voice>",
                f"        <type>{note_type}</type>",
                *(("        <dot/>",) if has_dot else ()),
                "      </note>",
            )
        return tuple(
            chain.from_iterable(
                map(
                    lambda idx_m: render_pitch_note(
                        idx_m[1], ev.ticks, idx_m[0] > 0, ev, lyr if idx_m[0] == 0 else ""
                    ),
                    enumerate(ev.pitches),
                )
            )
        )

    def render_bar(idx_pair: Tuple[int, Tuple[LeanBar, Tuple[str, ...]]]) -> Tuple[str, ...]:
        idx, (bar, lyrs) = idx_pair
        attrs = (
            (
                "      <attributes>",
                f"        <divisions>{TICKS_PER_QUARTER}</divisions>",
                f"        <key><fifths>{fifths}</fifths></key>",
                f"        <time><beats>{bar.beats}</beats><beat-type>{bar.beat_type}</beat-type></time>",
                "        <clef><sign>G</sign><line>2</line></clef>",
                "      </attributes>",
                "      <direction placement=\"above\">",
                "        <direction-type>",
                f"          <metronome><beat-unit>quarter</beat-unit><per-minute>{bpm_attr}</per-minute></metronome>",
                "        </direction-type>",
                f"        <sound tempo=\"{bpm_attr}\"/>",
                "      </direction>",
            )
            if idx == 0
            else ()
        )
        notes_xml = tuple(chain.from_iterable(map(render_event, zip(bar.events, lyrs))))
        return (f'    <measure number="{bar.bar_number}">', *attrs, *notes_xml, "    </measure>")

    measures_xml = tuple(chain.from_iterable(map(render_bar, enumerate(bars_with_lyrics))))
    lines = (
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">',
        '<score-partwise version="3.1">',
        f"  <work><work-title>{title}</work-title></work>",
        f'  <identification><creator type="composer">{composer}</creator></identification>',
        "  <part-list>",
        '    <score-part id="P1"><part-name>Melody (Sing / Lead)</part-name></score-part>',
        "  </part-list>",
        '  <part id="P1">',
        *measures_xml,
        "  </part>",
        "</score-partwise>",
    )
    return "\n".join(lines) + "\n"


def _lily_tempo_directive(bpm: float) -> str:
    """Format an exact integer LilyPond \\tempo directive when possible (e.g. 22.5 -> 8 = 45)."""
    frac = Fraction(max(5.0, float(bpm))).limit_denominator(16)
    if frac.denominator == 1:
        return f"\\tempo 4 = {frac.numerator}"
    if frac.denominator == 2:
        return f"\\tempo 8 = {frac.numerator}"
    if frac.denominator == 4:
        return f"\\tempo 16 = {frac.numerator}"
    return f"\\tempo 4 = {max(4, int(round(float(bpm))))}"


def export_lilypond(
    psalm_data: Dict[str, Any],
    speed: float = 1.0,
    augment: int = 1,
    pad_incomplete_bars: bool = True,
) -> str:
    """Generate GNU LilyPond 2.26 `.ly` source with both `\\layout {}` and `\\midi {}`."""
    title = str(psalm_data.get("title", "Psalm")).replace('"', "'")
    composer = str(psalm_data.get("composer", "Traditional")).replace('"', "'")
    fifths = _fifths_from_psalm(psalm_data)
    ly_key = FIFTHS_TO_LY_KEY.get(fifths, "c")
    eff_tempo = _effective_tempo(psalm_data, speed=speed)
    tempo_cmd = _lily_tempo_directive(eff_tempo)

    bars_with_lyrics = _build_rich_bars(
        psalm_data, speed=speed, augment=augment, pad_incomplete_bars=pad_incomplete_bars
    )
    if not bars_with_lyrics:
        ts_beats, ts_type = 4, 4
    else:
        ts_beats = bars_with_lyrics[0][0].beats
        ts_type = bars_with_lyrics[0][0].beat_type

    def fmt_event(ev: LeanEvent) -> str:
        dur = _ticks_to_ly_dur(ev.ticks)
        if ev.kind == "R" or not ev.pitches:
            return f"r{dur}"
        tie_sym = "~" if ev.tie_start else ""
        if len(ev.pitches) == 1:
            return f"{_midi_to_ly_pitch(ev.pitches[0], fifths)}{dur}{tie_sym}"
        chord_body = " ".join(map(lambda m: _midi_to_ly_pitch(m, fifths), ev.pitches))
        return f"<{chord_body}>{dur}{tie_sym}"

    def fmt_bar(pair: Tuple[LeanBar, Tuple[str, ...]]) -> str:
        bar, _ = pair
        return "    " + " ".join(map(fmt_event, bar.events)) + " |"

    bars_body = "\n".join(map(fmt_bar, bars_with_lyrics))
    subtitle_parts = tuple(
        filter(
            None,
            (
                f"Speed {speed * 100:.0f}%" if abs(speed - 1.0) > 1e-4 else "",
                f"Augment x{augment}" if int(augment) > 1 else "",
            ),
        )
    )
    subtitle = ", ".join(subtitle_parts) if subtitle_parts else "Original Score"

    return (
        '\\version "2.26.0"\n'
        "\\header {\n"
        f'  title = "{title}"\n'
        f'  subtitle = "{subtitle}"\n'
        f'  composer = "{composer}"\n'
        "  tagline = ##f\n"
        "}\n"
        "\\score {\n"
        "  \\new Staff {\n"
        '    \\clef "treble"\n'
        f"    \\key {ly_key} \\major\n"
        f"    \\time {ts_beats}/{ts_type}\n"
        f"    {tempo_cmd}\n"
        f"{bars_body}\n"
        '    \\bar "|."\n'
        "  }\n"
        "  \\layout { }\n"
        "  \\midi { }\n"
        "}\n"
    )


def _encode_varlen_rec(val: int, first: bool = True) -> bytes:
    byte = val & 0x7F
    if not first:
        byte |= 0x80
    rem = val >> 7
    if rem == 0:
        return bytes((byte,))
    return _encode_varlen_rec(rem, first=False) + bytes((byte,))


def _encode_varlen(val: int) -> bytes:
    return _encode_varlen_rec(max(0, int(val)), first=True)


def _flatten_sounding_events_for_playback(
    psalm_data: Dict[str, Any],
    speed: float = 1.0,
    augment: int = 1,
) -> Tuple[Tuple[LeanEvent, ...], float]:
    """Flatten bars into discrete sounding & rest events preserving ties cleanly."""
    bars = _build_rich_bars(psalm_data, speed=speed, augment=augment, pad_incomplete_bars=False)
    flat_evs = tuple(chain.from_iterable(map(lambda pair: pair[0].events, bars)))

    def step(
        acc: Tuple[list[LeanEvent], LeanEvent | None],
        ev: LeanEvent,
    ) -> Tuple[list[LeanEvent], LeanEvent | None]:
        out, prev = acc
        if prev is None:
            return out, ev
        if prev.kind == "N" and ev.kind == "N" and prev.tie_start and ev.tie_stop and prev.pitches == ev.pitches:
            merged = LeanEvent("N", prev.ticks + ev.ticks, ev.tie_start, prev.tie_stop, prev.pitches)
            return out, merged
        return [*out, prev], ev

    collected, last = reduce(step, flat_evs, ([], None))
    final_list = tuple([*collected, last]) if last is not None else ()
    return final_list, _effective_tempo(psalm_data, speed=speed)


def build_pure_python_midi(
    psalm_data: Dict[str, Any],
    speed: float = 1.0,
    augment: int = 1,
) -> bytes:
    """Pure Python Format-1 MIDI writer handling tempo scaling, rests, chords, and ties."""
    events, eff_tempo = _flatten_sounding_events_for_playback(psalm_data, speed=speed, augment=augment)
    microseconds_per_beat = max(50000, int(round(60_000_000.0 / eff_tempo)))
    ticks_per_beat = 480

    def step_bytes(acc: Tuple[bytes, int], ev: LeanEvent) -> Tuple[bytes, int]:
        chunk, pending_rest = acc
        dur_midi = int(round(float(Fraction(ev.ticks * ticks_per_beat, TICKS_PER_QUARTER))))
        if ev.kind == "R" or not ev.pitches:
            return chunk, pending_rest + dur_midi
        ons = b"".join(
            map(
                lambda idx_p: _encode_varlen(pending_rest if idx_p[0] == 0 else 0)
                + bytes((0x90, int(idx_p[1]) & 0x7F, 92)),
                enumerate(ev.pitches),
            )
        )
        offs = b"".join(
            map(
                lambda idx_p: _encode_varlen(dur_midi if idx_p[0] == 0 else 0)
                + bytes((0x80, int(idx_p[1]) & 0x7F, 0)),
                enumerate(ev.pitches),
            )
        )
        return chunk + ons + offs, 0

    notes_blob, _ = reduce(step_bytes, events, (b"", 0))
    header_events = (
        _encode_varlen(0)
        + b"\xFF\x51\x03"
        + struct.pack(">I", microseconds_per_beat)[1:]
        + _encode_varlen(0)
        + b"\xC0\x00"
    )
    end_of_track = _encode_varlen(0) + b"\xFF\x2F\x00"
    track_bytes = header_events + notes_blob + end_of_track
    header = struct.pack(">4sIHHH", b"MThd", 6, 1, 1, ticks_per_beat)
    track_header = struct.pack(">4sI", b"MTrk", len(track_bytes))
    return header + track_header + track_bytes


def export_midi(
    psalm_data: Dict[str, Any],
    speed: float = 1.0,
    augment: int = 1,
) -> bytes:
    """Generate Standard MIDI binary bytes (with speed scaling, rests, chords, and ties)."""
    if MIDO_AVAILABLE:
        try:
            events, eff_tempo = _flatten_sounding_events_for_playback(
                psalm_data, speed=speed, augment=augment
            )
            mid = MidiFile(ticks_per_beat=480)
            microseconds_per_beat = max(50000, int(round(60_000_000.0 / eff_tempo)))
            ts_parts = str(psalm_data.get("time_signature", "4/4")).split("/")
            aug_k = max(1, int(augment))
            ts_num = (int(ts_parts[0]) if ts_parts and ts_parts[0].isdigit() else 4) * aug_k
            ts_den = int(ts_parts[1]) if len(ts_parts) > 1 and ts_parts[1].isdigit() else 4

            melody_track = MidiTrack()
            mid.tracks.append(melody_track)
            melody_track.append(mido.MetaMessage("set_tempo", tempo=microseconds_per_beat, time=0))
            melody_track.append(mido.MetaMessage("time_signature", numerator=ts_num, denominator=ts_den, time=0))
            melody_track.append(mido.MetaMessage("track_name", name="Top Melody", time=0))
            melody_track.append(Message("program_change", program=0, channel=0, time=0))

            def add_ev_msgs(acc: Tuple[list[Message], int], ev: LeanEvent) -> Tuple[list[Message], int]:
                msgs, pending_rest = acc
                dur_midi = int(round(float(Fraction(ev.ticks * 480, TICKS_PER_QUARTER))))
                if ev.kind == "R" or not ev.pitches:
                    return msgs, pending_rest + dur_midi
                ons = list(
                    map(
                        lambda idx_p: Message(
                            "note_on",
                            note=int(idx_p[1]),
                            velocity=92,
                            channel=0,
                            time=pending_rest if idx_p[0] == 0 else 0,
                        ),
                        enumerate(ev.pitches),
                    )
                )
                offs = list(
                    map(
                        lambda idx_p: Message(
                            "note_off",
                            note=int(idx_p[1]),
                            velocity=0,
                            channel=0,
                            time=dur_midi if idx_p[0] == 0 else 0,
                        ),
                        enumerate(ev.pitches),
                    )
                )
                return [*msgs, *ons, *offs], 0

            msgs, _ = reduce(add_ev_msgs, events, ([], 0))
            deque(map(melody_track.append, msgs), maxlen=0)
            buffer = io.BytesIO()
            mid.save(file=buffer)
            res = buffer.getvalue()
            if res:
                return res
        except Exception:
            pass

    return build_pure_python_midi(psalm_data, speed=speed, augment=augment)


def _psalm_to_audio_events(
    psalm_data: Dict[str, Any],
    augment: int = 1,
    include_accompaniment: bool = True,
) -> Tuple[Tuple[AudioEvent, ...], Tuple[AudioEvent, ...]]:
    events, _ = _flatten_sounding_events_for_playback(psalm_data, speed=1.0, augment=augment)

    def step_mel(acc: Tuple[list[AudioEvent], float], ev: LeanEvent) -> Tuple[list[AudioEvent], float]:
        out, cursor_q = acc
        dur_q = float(ev.ticks) / float(TICKS_PER_QUARTER)
        if ev.kind == "N" and ev.pitches:
            return [*out, AudioEvent(cursor_q, dur_q, ev.pitches, 0.90)], cursor_q + dur_q
        return out, cursor_q + dur_q

    mel_events, _ = reduce(step_mel, events, ([], 0.0))

    if not include_accompaniment:
        return tuple(mel_events), ()

    aug_k = max(1, int(augment))
    raw_acc = psalm_data.get("response", {}).get("accompaniment", ())

    def step_acc(acc: Tuple[list[AudioEvent], float], ch: Dict[str, Any]) -> Tuple[list[AudioEvent], float]:
        out, cursor_q = acc
        dur_q = float(ch.get("beats", 2.0)) * aug_k
        chord_midis = tuple(map(int, ch.get("chord_midis", ())))
        bass_midi = ch.get("bass_midi")
        pitches = (*chord_midis, int(bass_midi)) if bass_midi is not None else chord_midis
        if pitches:
            return [*out, AudioEvent(cursor_q, dur_q, tuple(sorted(set(pitches))), 0.65)], cursor_q + dur_q
        return out, cursor_q + dur_q

    acc_events, _ = reduce(step_acc, raw_acc, ([], 0.0))
    return tuple(mel_events), tuple(acc_events)


def export_wav_bytes(
    psalm_data: Dict[str, Any],
    speed: float = 1.0,
    augment: int = 1,
    voice: str = "vocal_guide",
    include_accompaniment: bool = True,
    include_clicks: bool = True,
    count_in_bars: int = 1,
) -> bytes:
    """Render a `psalms_db` score into 16-bit PCM WAV bytes for singing along or practice."""
    mel_events, acc_events = _psalm_to_audio_events(
        psalm_data, augment=augment, include_accompaniment=include_accompaniment
    )
    eff_tempo = _effective_tempo(psalm_data, speed=speed)
    ts_parts = str(psalm_data.get("time_signature", "4/4")).split("/")
    aug_k = max(1, int(augment))
    ts_num = (int(ts_parts[0]) if ts_parts and ts_parts[0].isdigit() else 4) * aug_k
    ts_den = ts_parts[1] if len(ts_parts) > 1 else "4"
    return render_wav_bytes(
        melody_events=mel_events,
        time_signature=f"{ts_num}/{ts_den}",
        tempo_bpm=eff_tempo,
        voice=voice,
        accompaniment_events=acc_events,
        include_clicks=include_clicks,
        count_in_bars=count_in_bars,
    )


# <!-- APAF Bioinformatics | score_formatter.py | Approved | 2026-11-15 -->
