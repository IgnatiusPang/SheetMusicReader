"""Unified PDF / Image / MusicXML / JSON -> LilyPond + MuseScore + MIDI + Sing-Along + Lean 4 pipeline.

CLI subcommands:
- convert: Convert a score into synchronized MusicXML, LilyPond (.ly / optional .pdf),
  MIDI, and Sing-Along WAV (optional MP3) across original and slow-practice editions,
  verified against Lean 4 (`score_verifier` and optional `.lean` kernel certificate).
- sing: Quickly generate and optionally play a Vocal Guide + count-in + beat-click track.
- verify: Independently re-parse generated formats from disk and check Lean 4 equivalence.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
from collections import deque
from dataclasses import replace
from fractions import Fraction
from functools import reduce
from itertools import chain
from pathlib import Path
from typing import Any, Sequence
from xml.sax.saxutils import escape as xml_escape

import mido
from mido import Message, MidiFile, MidiTrack

import score_formatter
import vector_omr
from audio_synth import AudioEvent, convert_wav_to_mp3, play_wav, render_wav_bytes
from lean_bridge import (
    LeanBar,
    LeanEvent,
    LeanScoreSpec,
    TICKS_PER_QUARTER,
    float_to_ratio,
    spec_from_lilypond_file,
    spec_from_musicxml_file,
    spec_from_psalm_data,
    spec_from_vector_score,
    sounding_notes_from_midi_file,
    verify_bundle_with_lean,
)

FIFTHS_TO_KEY_NAME = {
    0: "C Major", 1: "G Major", 2: "D Major", 3: "A Major", 4: "E Major",
    5: "B Major", 6: "F# Major", 7: "C# Major",
    -1: "F Major", -2: "Bb Major", -3: "Eb Major", -4: "Ab Major",
    -5: "Db Major", -6: "Gb Major", -7: "Cb Major",
}


def parse_rational(raw: str | float) -> Fraction:
    """Parse decimal or rational speed like `'0.5'`, `'1/3'`, `'0.25'`."""
    s = str(raw).strip()
    if "/" in s:
        num_s, den_s = s.split("/", 1)
        return Fraction(int(num_s.strip()), int(den_s.strip()))
    return Fraction(float(s)).limit_denominator(1000)


def slugify_speed(speed: Fraction, augment: int) -> str:
    pct = int(round(float(speed) * 100.0))
    aug_part = f"_aug{augment}x" if augment > 1 else ""
    if speed == 1 and augment <= 1:
        return "original"
    return f"speed_{pct}pct{aug_part}"


def scale_spec_tempo_and_augment(
    spec: LeanScoreSpec,
    speed: Fraction,
    augment: int = 1,
) -> LeanScoreSpec:
    """Mirror Lean `scaleTempo` and `augmentScore` on a Python `LeanScoreSpec`."""
    aug_k = max(1, int(augment))
    s_num = max(1, int(speed.numerator))
    s_den = max(1, int(speed.denominator))

    def aug_ev(ev: LeanEvent) -> LeanEvent:
        return LeanEvent(ev.kind, ev.ticks * aug_k, ev.tie_start, ev.tie_stop, ev.pitches)

    def aug_bar(b: LeanBar) -> LeanBar:
        return LeanBar(
            b.bar_number,
            b.beats * aug_k,
            b.beat_type,
            b.expected_ticks * aug_k,
            tuple(map(aug_ev, b.events)),
        )

    raw_num = spec.tempo_num * s_num
    raw_den = spec.tempo_den * s_den
    g = Fraction(raw_num, raw_den)
    return LeanScoreSpec(
        title=spec.title,
        tempo_num=int(g.numerator),
        tempo_den=int(g.denominator),
        bars=tuple(map(aug_bar, spec.bars)) if aug_k > 1 else spec.bars,
    )


def pad_spec_bars_with_rests(spec: LeanScoreSpec) -> LeanScoreSpec:
    """Apply Lean `appendRest` completion to any under-filled bars."""
    def pad_bar(b: LeanBar) -> LeanBar:
        actual = sum(map(lambda e: e.ticks, b.events))
        if actual < b.expected_ticks:
            rest = LeanEvent("R", b.expected_ticks - actual, False, False, ())
            return LeanBar(b.bar_number, b.beats, b.beat_type, b.expected_ticks, (*b.events, rest))
        return b

    return LeanScoreSpec(spec.title, spec.tempo_num, spec.tempo_den, tuple(map(pad_bar, spec.bars)))


def load_score_input(
    input_path: Path,
    lane: int = 0,
    pad_rests: bool = False,
    arrangement: bool = False,
) -> tuple[LeanScoreSpec, int, dict[str, Any] | None]:
    """Load `.pdf`, `.json`, `.musicxml`/`.xml`, `.ly`, or image into `(LeanScoreSpec, key_fifths, optional_psalm_dict)`."""
    input_path = Path(input_path)
    ext = input_path.suffix.lower()

    if ext == ".json":
        psalm_data = json.loads(input_path.read_text(encoding="utf-8"))
        fifths = score_formatter._fifths_from_psalm(psalm_data)
        spec = spec_from_psalm_data(psalm_data, pad_incomplete_bars=pad_rests or True)
        return spec, fifths, psalm_data

    if ext in (".musicxml", ".xml"):
        spec = spec_from_musicxml_file(input_path)
        import xml.etree.ElementTree as ET
        fifths_el = ET.parse(input_path).getroot().find(".//attributes/key/fifths")
        fifths = int(fifths_el.text.strip()) if (fifths_el is not None and fifths_el.text) else 0
        if pad_rests:
            spec = pad_spec_bars_with_rests(spec)
        return spec, fifths, None

    if ext == ".ly":
        spec = spec_from_lilypond_file(input_path)
        txt = input_path.read_text(encoding="utf-8")
        key_m = re.search(r"\\key\s+([a-z]+)\s+\\major", txt)
        inv_map = dict(map(lambda kv: (kv[1], kv[0]), score_formatter.FIFTHS_TO_LY_KEY.items()))
        fifths = inv_map.get(key_m.group(1), 0) if key_m else 0
        if pad_rests:
            spec = pad_spec_bars_with_rests(spec)
        return spec, fifths, None

    if ext == ".pdf":
        sc = vector_omr.read_score(input_path)
        if sc.systems:
            spec = spec_from_vector_score(sc, lane=lane, arrangement=arrangement)
            first_m = next(
                chain.from_iterable(map(lambda sys: sys[lane].measures if lane < len(sys) else (), sc.systems)),
                None,
            )
            fifths = int(first_m.key) if first_m is not None else 0
            if pad_rests:
                spec = pad_spec_bars_with_rests(spec)
            return spec, fifths, None

    # Fallback for scanned PDF or raster image (.png/.jpg/.jpeg/.tif)
    import score_from_image

    work_out = input_path.parent / "_omr_work"
    res = score_from_image.convert(input_path, work_out)
    ly_file = res.get("ly")
    if ly_file and Path(ly_file).is_file():
        spec = spec_from_lilypond_file(Path(ly_file))
        if pad_rests:
            spec = pad_spec_bars_with_rests(spec)
        return spec, 0, None
    raise RuntimeError(f"Could not extract symbolic music from {input_path}")


def spec_to_musicxml(spec: LeanScoreSpec, fifths: int = 0) -> str:
    """Render any `LeanScoreSpec` directly to MusicXML 3.1 matching Lean integer ticks."""
    bpm = float(spec.tempo_num) / float(max(1, spec.tempo_den))
    bpm_attr = f"{bpm:.2f}".rstrip("0").rstrip(".")

    def render_pitch_ev(ev: LeanEvent, midi: int, is_chord: bool) -> tuple[str, ...]:
        step, alter, octv = score_formatter._parse_pitch_parts("", midi)
        ntype, has_dot = score_formatter._ticks_to_xml_type(ev.ticks)
        ties = (
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
            f"        <duration>{ev.ticks}</duration>",
            *map(lambda t: f"        {t}", ties),
            "        <voice>1</voice>",
            f"        <type>{ntype}</type>",
            *(("        <dot/>",) if has_dot else ()),
            *(("        <notations>", *map(lambda t: f"          {t}", notations), "        </notations>") if notations else ()),
            "      </note>",
        )

    def render_ev(ev: LeanEvent) -> tuple[str, ...]:
        if ev.kind == "R" or not ev.pitches:
            ntype, has_dot = score_formatter._ticks_to_xml_type(ev.ticks)
            return (
                "      <note>",
                "        <rest/>",
                f"        <duration>{ev.ticks}</duration>",
                "        <voice>1</voice>",
                f"        <type>{ntype}</type>",
                *(("        <dot/>",) if has_dot else ()),
                "      </note>",
            )
        return tuple(
            chain.from_iterable(
                map(lambda ip: render_pitch_ev(ev, ip[1], ip[0] > 0), enumerate(ev.pitches))
            )
        )

    def render_bar(idx_b: tuple[int, LeanBar]) -> tuple[str, ...]:
        idx, bar = idx_b
        prev_b = spec.bars[idx - 1] if idx > 0 else None
        sig_changed = prev_b is None or (prev_b.beats, prev_b.beat_type) != (bar.beats, bar.beat_type)
        attrs = (
            (
                "      <attributes>",
                *((f"        <divisions>{TICKS_PER_QUARTER}</divisions>", f"        <key><fifths>{fifths}</fifths></key>") if idx == 0 else ()),
                f"        <time><beats>{bar.beats}</beats><beat-type>{bar.beat_type}</beat-type></time>",
                *(("        <clef><sign>G</sign><line>2</line></clef>",) if idx == 0 else ()),
                "      </attributes>",
            )
            if sig_changed
            else ()
        )
        tempo_dir = (
            (
                '      <direction placement="above">',
                "        <direction-type>",
                f"          <metronome><beat-unit>quarter</beat-unit><per-minute>{bpm_attr}</per-minute></metronome>",
                "        </direction-type>",
                f'        <sound tempo="{bpm_attr}"/>',
                "      </direction>",
            )
            if idx == 0
            else ()
        )
        notes_xml = tuple(chain.from_iterable(map(render_ev, bar.events)))
        return (f'    <measure number="{bar.bar_number}">', *attrs, *tempo_dir, *notes_xml, "    </measure>")

    measures_xml = tuple(chain.from_iterable(map(render_bar, enumerate(spec.bars))))
    return "\n".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" '
            '"http://www.musicxml.org/dtds/partwise.dtd">',
            '<score-partwise version="3.1">',
            f"  <work><work-title>{xml_escape(spec.title)}</work-title></work>",
            "  <part-list>",
            '    <score-part id="P1"><part-name>Melody (Sing / Lead)</part-name></score-part>',
            "  </part-list>",
            '  <part id="P1">',
            *measures_xml,
            "  </part>",
            "</score-partwise>",
        )
    ) + "\n"


def spec_to_lilypond(spec: LeanScoreSpec, fifths: int = 0, subtitle: str = "") -> str:
    """Render any `LeanScoreSpec` directly to GNU LilyPond 2.26 with `\\layout {}` and `\\midi {}`."""
    ly_key = score_formatter.FIFTHS_TO_LY_KEY.get(fifths, "c")
    bpm = float(spec.tempo_num) / float(max(1, spec.tempo_den))
    tempo_cmd = score_formatter._lily_tempo_directive(bpm)

    def fmt_ev(ev: LeanEvent) -> str:
        dur = score_formatter._ticks_to_ly_dur(ev.ticks)
        if ev.kind == "R" or not ev.pitches:
            return f"r{dur}"
        tie_sym = "~" if ev.tie_start else ""
        if len(ev.pitches) == 1:
            return f"{score_formatter._midi_to_ly_pitch(ev.pitches[0], fifths)}{dur}{tie_sym}"
        chord_body = " ".join(map(lambda m: score_formatter._midi_to_ly_pitch(m, fifths), ev.pitches))
        return f"<{chord_body}>{dur}{tie_sym}"

    def fmt_bar(idx_b: tuple[int, LeanBar]) -> str:
        idx, bar = idx_b
        prev_b = spec.bars[idx - 1] if idx > 0 else None
        sig = f"\\time {bar.beats}/{bar.beat_type} " if (prev_b is None or (prev_b.beats, prev_b.beat_type) != (bar.beats, bar.beat_type)) else ""
        return "    " + sig + " ".join(map(fmt_ev, bar.events)) + " |"

    bars_body = "\n".join(map(fmt_bar, enumerate(spec.bars)))
    safe_title = spec.title.replace('"', "'")
    sub = subtitle or "Lean-Verified Edition"
    return (
        '\\version "2.26.0"\n'
        "\\header {\n"
        f'  title = "{safe_title}"\n'
        f'  subtitle = "{sub}"\n'
        "  tagline = ##f\n"
        "}\n"
        "\\score {\n"
        "  \\new Staff {\n"
        '    \\clef "treble"\n'
        f"    \\key {ly_key} \\major\n"
        f"    {tempo_cmd}\n"
        f"{bars_body}\n"
        '    \\bar "|."\n'
        "  }\n"
        "  \\layout { }\n"
        "  \\midi { }\n"
        "}\n"
    )


def _merge_ties_for_audio_and_midi(spec: LeanScoreSpec) -> tuple[LeanEvent, ...]:
    flat = tuple(chain.from_iterable(map(lambda b: b.events, spec.bars)))

    def step(
        acc: tuple[list[LeanEvent], LeanEvent | None],
        ev: LeanEvent,
    ) -> tuple[list[LeanEvent], LeanEvent | None]:
        out, prev = acc
        if prev is None:
            return out, ev
        if prev.kind == "N" and ev.kind == "N" and prev.tie_start and ev.tie_stop and prev.pitches == ev.pitches:
            return out, LeanEvent("N", prev.ticks + ev.ticks, ev.tie_start, prev.tie_stop, prev.pitches)
        return [*out, prev], ev

    collected, last = reduce(step, flat, ([], None))
    return tuple([*collected, last]) if last is not None else ()


def spec_to_midi_bytes(spec: LeanScoreSpec) -> bytes:
    """Serialize any `LeanScoreSpec` to Standard MIDI bytes preserving rests and merged ties."""
    events = _merge_ties_for_audio_and_midi(spec)
    bpm = max(5.0, float(spec.tempo_num) / float(max(1, spec.tempo_den)))
    us_per_beat = max(50000, int(round(60_000_000.0 / bpm)))
    first_bar = spec.bars[0] if spec.bars else LeanBar(1, 4, 4, 192, ())

    mid = MidiFile(ticks_per_beat=480)
    tr = MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=us_per_beat, time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=first_bar.beats, denominator=first_bar.beat_type, time=0))
    tr.append(mido.MetaMessage("track_name", name="Melody (Lead)", time=0))
    tr.append(Message("program_change", program=0, channel=0, time=0))

    def add_msgs(acc: tuple[list[Message], int], ev: LeanEvent) -> tuple[list[Message], int]:
        msgs, pending_rest = acc
        dur_midi = int(round(float(Fraction(ev.ticks * 480, TICKS_PER_QUARTER))))
        if ev.kind == "R" or not ev.pitches:
            return msgs, pending_rest + dur_midi
        ons = list(
            map(
                lambda ip: Message("note_on", note=int(ip[1]), velocity=92, channel=0, time=pending_rest if ip[0] == 0 else 0),
                enumerate(ev.pitches),
            )
        )
        offs = list(
            map(
                lambda ip: Message("note_off", note=int(ip[1]), velocity=0, channel=0, time=dur_midi if ip[0] == 0 else 0),
                enumerate(ev.pitches),
            )
        )
        return [*msgs, *ons, *offs], 0

    msgs, _ = reduce(add_msgs, events, ([], 0))
    deque(map(tr.append, msgs), maxlen=0)
    buf = io.BytesIO()
    mid.save(file=buf)
    return buf.getvalue()


def spec_to_wav_bytes(
    spec: LeanScoreSpec,
    voice: str = "vocal_guide",
    include_clicks: bool = True,
    count_in_bars: int = 1,
    accompaniment_events: Sequence[AudioEvent] = (),
) -> bytes:
    """Synthesize a `LeanScoreSpec` directly into 16-bit PCM WAV bytes."""
    events = _merge_ties_for_audio_and_midi(spec)

    def step_ev(acc: tuple[list[AudioEvent], float], ev: LeanEvent) -> tuple[list[AudioEvent], float]:
        out, cursor_q = acc
        dur_q = float(ev.ticks) / float(TICKS_PER_QUARTER)
        if ev.kind == "N" and ev.pitches:
            return [*out, AudioEvent(cursor_q, dur_q, ev.pitches, 0.90)], cursor_q + dur_q
        return out, cursor_q + dur_q

    mel_events, _ = reduce(step_ev, events, ([], 0.0))
    first_bar = spec.bars[0] if spec.bars else LeanBar(1, 4, 4, 192, ())
    bpm = max(5.0, float(spec.tempo_num) / float(max(1, spec.tempo_den)))
    return render_wav_bytes(
        melody_events=mel_events,
        time_signature=f"{first_bar.beats}/{first_bar.beat_type}",
        tempo_bpm=bpm,
        voice=voice,
        accompaniment_events=accompaniment_events,
        include_clicks=include_clicks,
        count_in_bars=count_in_bars,
    )


def compile_lilypond_pdf(ly_path: Path, out_dir: Path) -> Path | None:
    """Invoke GNU LilyPond to render a `.ly` file into `.pdf`."""
    ly_bin = shutil.which("lilypond")
    if not ly_bin:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    stem_out = out_dir / ly_path.stem
    proc = subprocess.run(
        [ly_bin, "-dno-point-and-click", "-o", str(stem_out), str(ly_path)],
        capture_output=True,
        text=True,
    )
    pdf_out = out_dir / f"{ly_path.stem}.pdf"
    return pdf_out if proc.returncode == 0 and pdf_out.is_file() else None


def run_convert_pipeline(
    input_path: Path,
    out_dir: Path,
    speeds: Sequence[Fraction] = (Fraction(1, 1),),
    augment: int = 1,
    voice: str = "vocal_guide",
    count_in_bars: int = 1,
    include_clicks: bool = True,
    render_pdf: bool = False,
    export_mp3: bool = False,
    lean_cert: bool = False,
    pad_rests: bool = False,
    arrangement: bool = False,
    accompaniment: bool = True,
) -> dict[str, Any]:
    """Convert an input score into synchronized MusicXML, LilyPond, MIDI, WAV, and Lean verification."""
    input_path = Path(input_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base_spec, fifths, psalm_data = load_score_input(input_path, pad_rests=pad_rests, arrangement=arrangement)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", input_path.stem)

    base_accomp_events: tuple[AudioEvent, ...] = ()
    if psalm_data is None and accompaniment and input_path.suffix.lower() == ".pdf":
        import karaoke_trainer

        k_data = karaoke_trainer.extract_karaoke_score_from_pdf(input_path)
        target_mode = "full_arrangement" if arrangement else "chart_as_written"
        mode_obj = next(
            filter(lambda m: m.get("mode_id") == target_mode, k_data.get("modes", ())),
            None,
        )
        if mode_obj and mode_obj.get("chords"):
            base_accomp_events = karaoke_trainer.chords_to_audio_events(
                mode_obj["chords"],
                str(k_data.get("time_signature", "4/4")),
            )

    def emit_edition(speed: Fraction) -> dict[str, Any]:
        tag = slugify_speed(speed, augment if speed != 1 or augment > 1 else 1)
        aug_k = augment if (speed != 1 or augment > 1) else 1
        ed_spec = scale_spec_tempo_and_augment(base_spec, speed, augment=aug_k)
        s_float = float(speed)

        xml_path = out_dir / f"{stem}_{tag}.musicxml"
        ly_path = out_dir / f"{stem}_{tag}.ly"
        mid_path = out_dir / f"{stem}_{tag}.mid"
        wav_path = out_dir / f"{stem}_{tag}.wav"

        if psalm_data is not None:
            xml_text = score_formatter.export_musicxml(psalm_data, speed=s_float, augment=aug_k)
            ly_text = score_formatter.export_lilypond(psalm_data, speed=s_float, augment=aug_k)
            mid_bytes = score_formatter.export_midi(psalm_data, speed=s_float, augment=aug_k)
            wav_bytes = score_formatter.export_wav_bytes(
                psalm_data,
                speed=s_float,
                augment=aug_k,
                voice=voice,
                include_accompaniment=accompaniment,
                include_clicks=include_clicks,
                count_in_bars=count_in_bars,
            )
        else:
            xml_text = spec_to_musicxml(ed_spec, fifths=fifths)
            ly_text = spec_to_lilypond(ed_spec, fifths=fifths, subtitle=tag.replace("_", " "))
            mid_bytes = spec_to_midi_bytes(ed_spec)
            accomp_evs = (
                tuple(
                    map(
                        lambda ev: AudioEvent(
                            ev.onset_beats * aug_k,
                            ev.duration_beats * aug_k,
                            ev.pitches,
                            ev.velocity,
                        ),
                        base_accomp_events,
                    )
                )
                if (aug_k > 1 and base_accomp_events)
                else base_accomp_events
            )
            wav_bytes = spec_to_wav_bytes(
                ed_spec,
                voice=voice,
                include_clicks=include_clicks,
                count_in_bars=count_in_bars,
                accompaniment_events=accomp_evs,
            )

        xml_path.write_text(xml_text, encoding="utf-8")
        ly_path.write_text(ly_text, encoding="utf-8")
        mid_path.write_bytes(mid_bytes)
        wav_path.write_bytes(wav_bytes)

        mp3_path = convert_wav_to_mp3(wav_path) if export_mp3 else None
        pdf_path = compile_lilypond_pdf(ly_path, out_dir) if render_pdf else None

        # Gate D5: Re-parse actual written disk files independently before Lean verification
        parsed_xml = spec_from_musicxml_file(xml_path)
        parsed_ly = spec_from_lilypond_file(ly_path)
        midi_notes, midi_tnum, midi_tden = sounding_notes_from_midi_file(mid_path)

        return {
            "tag": tag,
            "speed": str(speed),
            "augment": aug_k,
            "musicxml": str(xml_path),
            "lilypond": str(ly_path),
            "midi": str(mid_path),
            "wav": str(wav_path),
            "mp3": str(mp3_path) if mp3_path else None,
            "pdf": str(pdf_path) if pdf_path else None,
            "_score_entries": (
                (f"{tag}_musicxml", parsed_xml, aug_k, int(speed.numerator), int(speed.denominator)),
                (f"{tag}_lilypond", parsed_ly, aug_k, int(speed.numerator), int(speed.denominator)),
            ),
            "_note_entries": (
                (f"{tag}_midi", midi_notes, aug_k, int(speed.numerator), int(speed.denominator), midi_tnum, midi_tden),
            ),
        }

    editions_raw = tuple(map(emit_edition, speeds))
    score_entries = tuple(chain.from_iterable(map(lambda ed: ed["_score_entries"], editions_raw)))
    note_entries = tuple(chain.from_iterable(map(lambda ed: ed["_note_entries"], editions_raw)))
    cert_file = (out_dir / f"{stem}_cert.lean") if lean_cert else None

    lean_report = verify_bundle_with_lean(
        reference=("original", base_spec),
        score_entries=score_entries,
        note_entries=note_entries,
        cert_path=cert_file,
    )

    editions_clean = tuple(
        map(
            lambda ed: dict(filter(lambda kv: not kv[0].startswith("_"), ed.items())),
            editions_raw,
        )
    )
    return {
        "input": str(input_path),
        "title": base_spec.title,
        "base_tempo_bpm": float(base_spec.tempo_num) / float(max(1, base_spec.tempo_den)),
        "editions": list(editions_clean),
        "lean_verification": lean_report,
    }


def _resolve_speeds(args: argparse.Namespace, base_bpm: float) -> tuple[Fraction, ...]:
    if getattr(args, "bpm", None) is not None:
        return (Fraction(float(args.bpm), max(1.0, base_bpm)).limit_denominator(1000),)
    if getattr(args, "speeds", None):
        return tuple(map(parse_rational, filter(None, map(str.strip, args.speeds.split(",")))))
    return (parse_rational(getattr(args, "speed", "1")),)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SheetMusicReader unified conversion, sing-along, and Lean 4 verification CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_conv = sub.add_parser("convert", help="Convert score to MusicXML, LilyPond, MIDI, WAV, and verify with Lean 4")
    p_conv.add_argument("input", type=Path)
    p_conv.add_argument("--out-dir", type=Path, default=Path("practice_output"))
    p_conv.add_argument("--speed", default="1.0", help="Playback speed fraction or decimal (e.g. 0.5, 1/3, 0.25)")
    p_conv.add_argument("--speeds", default=None, help="Comma-separated speeds (e.g. 1.0,0.5,0.25)")
    p_conv.add_argument("--bpm", type=float, default=None, help="Target quarter-note BPM")
    p_conv.add_argument("--augment", type=int, default=1, help="Multiply written note values by integer k (e.g. 2)")
    p_conv.add_argument("--voice", choices=["vocal_guide", "piano", "violin"], default="vocal_guide")
    p_conv.add_argument("--count-in", type=int, default=1, help="Count-in bars before playback")
    p_conv.add_argument("--no-clicks", action="store_true")
    p_conv.add_argument("--no-accompaniment", action="store_true", help="Omit chord backing accompaniment from WAV/MP3")
    p_conv.add_argument("--render-pdf", action="store_true")
    p_conv.add_argument("--mp3", action="store_true")
    p_conv.add_argument("--lean-cert", action="store_true")
    p_conv.add_argument("--pad-rests", action="store_true", help="Complete under-filled bars with silent rests")
    p_conv.add_argument(
        "--arrangement",
        action="store_true",
        help="Expand Responsorial Psalm sections (R -> V1 -> R -> V2 -> ... -> Final R) with exact meter-conserving pickups",
    )

    p_sing = sub.add_parser("sing", help="Generate (and optionally play) a Vocal Guide WAV practice track")
    p_sing.add_argument("input", type=Path)
    p_sing.add_argument("--out-dir", type=Path, default=Path("sing_output"))
    p_sing.add_argument("--speed", default="0.5")
    p_sing.add_argument("--bpm", type=float, default=None)
    p_sing.add_argument("--augment", type=int, default=1)
    p_sing.add_argument("--voice", choices=["vocal_guide", "piano", "violin"], default="vocal_guide")
    p_sing.add_argument("--count-in", type=int, default=1)
    p_sing.add_argument("--no-clicks", action="store_true")
    p_sing.add_argument("--no-accompaniment", action="store_true", help="Omit chord backing accompaniment from WAV/MP3")
    p_sing.add_argument("--mp3", action="store_true")
    p_sing.add_argument("--play", action="store_true")
    p_sing.add_argument("--pad-rests", action="store_true")
    p_sing.add_argument(
        "--arrangement",
        action="store_true",
        help="Expand Responsorial Psalm sections (R -> V1 -> R -> V2 -> ... -> Final R) with exact meter-conserving pickups",
    )

    p_kar = sub.add_parser("karaoke", help="Generate standalone interactive HTML5 Karaoke Note + Word Trainer")
    p_kar.add_argument("input", type=Path)
    p_kar.add_argument("--out", type=Path, default=None, help="Output HTML file path")

    p_ver = sub.add_parser("verify", help="Verify score representations via Lean 4 score_verifier")
    p_ver.add_argument("input", type=Path)
    p_ver.add_argument("--musicxml", type=Path, default=None)
    p_ver.add_argument("--lilypond", type=Path, default=None)
    p_ver.add_argument("--midi", type=Path, default=None)
    p_ver.add_argument("--speed", default="1.0")
    p_ver.add_argument("--augment", type=int, default=1)
    p_ver.add_argument("--lean-cert", type=Path, default=None)
    p_ver.add_argument("--pad-rests", action="store_true")
    p_ver.add_argument(
        "--arrangement",
        action="store_true",
        help="Expand Responsorial Psalm sections (R -> V1 -> R -> V2 -> ... -> Final R) with exact meter-conserving pickups",
    )

    args = parser.parse_args(argv)

    if args.cmd == "karaoke":
        import karaoke_trainer

        stem = re.sub(r"[^A-Za-z0-9_-]+", "_", args.input.stem)
        out_html = args.out if args.out is not None else args.input.with_name(f"{stem}_Karaoke_Trainer.html")
        written, data = karaoke_trainer.export_karaoke_html(args.input, out_html)
        print(
            json.dumps(
                {
                    "ok": True,
                    "out": str(written),
                    "title": data.get("title"),
                    "modes": list(map(lambda m: m.get("mode_id"), data.get("modes", ()))),
                },
                indent=2,
            )
        )
        return 0

    if args.cmd == "verify":
        base_spec, _, _ = load_score_input(args.input, pad_rests=args.pad_rests, arrangement=args.arrangement)
        sp = parse_rational(args.speed)
        aug = max(1, int(args.augment))
        scores = tuple(
            filter(
                None,
                (
                    ("musicxml", spec_from_musicxml_file(args.musicxml), aug, int(sp.numerator), int(sp.denominator)) if args.musicxml else None,
                    ("lilypond", spec_from_lilypond_file(args.lilypond), aug, int(sp.numerator), int(sp.denominator)) if args.lilypond else None,
                ),
            )
        )
        midi_parsed = sounding_notes_from_midi_file(args.midi) if args.midi else None
        notes = (
            (("midi", midi_parsed[0], aug, int(sp.numerator), int(sp.denominator), midi_parsed[1], midi_parsed[2]),)
            if midi_parsed is not None
            else ()
        )
        rep = verify_bundle_with_lean(
            reference=("original", base_spec),
            score_entries=scores,
            note_entries=notes,
            cert_path=args.lean_cert,
        )
        print(json.dumps(rep, indent=2))
        return 0 if rep.get("ok") else 1

    base_spec, _, _ = load_score_input(args.input, pad_rests=args.pad_rests, arrangement=args.arrangement)
    base_bpm = float(base_spec.tempo_num) / float(max(1, base_spec.tempo_den))
    speeds = _resolve_speeds(args, base_bpm)

    if args.cmd == "sing":
        rep = run_convert_pipeline(
            args.input,
            args.out_dir,
            speeds=speeds,
            augment=max(1, int(args.augment)),
            voice=args.voice,
            count_in_bars=max(0, int(args.count_in)),
            include_clicks=not args.no_clicks,
            render_pdf=False,
            export_mp3=args.mp3,
            lean_cert=False,
            pad_rests=args.pad_rests,
            arrangement=args.arrangement,
            accompaniment=not args.no_accompaniment,
        )
        print(json.dumps(rep, indent=2))
        if args.play and rep["editions"]:
            play_wav(Path(rep["editions"][0]["wav"]))
        return 0 if rep["lean_verification"].get("ok") else 1

    rep = run_convert_pipeline(
        args.input,
        args.out_dir,
        speeds=speeds,
        augment=max(1, int(args.augment)),
        voice=args.voice,
        count_in_bars=max(0, int(args.count_in)),
        include_clicks=not args.no_clicks,
        render_pdf=args.render_pdf,
        export_mp3=args.mp3,
        lean_cert=args.lean_cert,
        pad_rests=args.pad_rests,
        arrangement=args.arrangement,
        accompaniment=not args.no_accompaniment,
    )
    print(json.dumps(rep, indent=2))
    return 0 if rep["lean_verification"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())


# <!-- APAF Bioinformatics | music_pipeline.py | Approved | 2026-11-15 -->
