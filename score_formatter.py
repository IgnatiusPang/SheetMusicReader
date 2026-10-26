import os
import io
import struct
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

try:
    import mido
    from mido import MidiFile, MidiTrack, Message
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False


def export_musicxml(psalm_data: Dict[str, Any]) -> str:
    """Generates standard MusicXML for the given digitized psalm score."""
    title = psalm_data.get("title", "Psalm")
    composer = psalm_data.get("composer", "Traditional")
    key_sig = psalm_data.get("key", "C Major")
    time_sig = psalm_data.get("time_signature", "4/4")
    tempo = psalm_data.get("tempo", 100)
    
    response = psalm_data.get("response", {})
    notes = response.get("notes", [])

    time_parts = time_sig.split("/")
    beats_per_measure = time_parts[0] if len(time_parts) > 0 else "4"
    beat_type = time_parts[1] if len(time_parts) > 1 else "4"

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">',
        '<score-partwise version="3.1">',
        '  <work><work-title>' + title + '</work-title></work>',
        '  <identification><creator type="composer">' + composer + '</creator></identification>',
        '  <part-list>',
        '    <score-part id="P1"><part-name>Top Melody</part-name></score-part>',
        '  </part-list>',
        '  <part id="P1">',
        '    <measure number="1">',
        '      <attributes>',
        '        <divisions>4</divisions>',
        '        <key><fifths>0</fifths></key>',
        f'        <time><beats>{beats_per_measure}</beats><beat-type>{beat_type}</beat-type></time>',
        '        <clef><sign>G</sign><line>2</line></clef>',
        '      </attributes>',
        f'      <direction placement="above"><direction-type><metronome><beat-unit>quarter</beat-unit><per-minute>{tempo}</per-minute></metronome></direction-type></direction>'
    ]

    measure_num = 1
    current_beats = 0.0
    beats_limit = float(beats_per_measure) if beats_per_measure.isdigit() else 4.0

    for n in notes:
        dur_beats = float(n.get("beats", 1.0))
        divisions_dur = int(dur_beats * 4)
        pitch = n.get("pitch", "C4")
        lyric = n.get("lyric", "")
        
        step = pitch[0]
        octave = pitch[-1] if pitch[-1].isdigit() else "4"
        alter = 0
        if "#" in pitch or "♯" in pitch:
            alter = 1
        elif "b" in pitch or "♭" in pitch:
            alter = -1

        if current_beats + dur_beats > beats_limit and current_beats > 0:
            measure_num += 1
            xml_lines.append('    </measure>')
            xml_lines.append(f'    <measure number="{measure_num}">')
            current_beats = 0.0

        xml_lines.append('      <note>')
        xml_lines.append('        <pitch>')
        xml_lines.append(f'          <step>{step}</step>')
        if alter != 0:
            xml_lines.append(f'          <alter>{alter}</alter>')
        xml_lines.append(f'          <octave>{octave}</octave>')
        xml_lines.append('        </pitch>')
        xml_lines.append(f'        <duration>{divisions_dur}</duration>')
        xml_lines.append(f'        <type>{n.get("duration", "quarter")}</type>')
        if lyric:
            xml_lines.append(f'        <lyric><text>{lyric}</text></lyric>')
        xml_lines.append('      </note>')
        
        current_beats += dur_beats

    xml_lines.append('    </measure>')
    xml_lines.append('  </part>')
    xml_lines.append('</score-partwise>')

    return "\n".join(xml_lines)


def _encode_varlen(val: int) -> bytes:
    buf = bytearray()
    buf.append(val & 0x7F)
    val >>= 7
    while val > 0:
        buf.insert(0, (val & 0x7F) | 0x80)
        val >>= 7
    return bytes(buf)


def build_pure_python_midi(psalm_data: Dict[str, Any]) -> bytes:
    """Pure Python fallback MIDI file writer (Format 1)."""
    tempo_bpm = int(psalm_data.get("tempo", 100))
    microseconds_per_beat = int(60000000 / tempo_bpm)
    ticks_per_beat = 480

    notes = psalm_data.get("response", {}).get("notes", [])
    
    track_bytes = bytearray()
    
    # Set tempo event: delta=0, meta=0xFF 0x51 0x03 [3-byte tempo]
    track_bytes.extend(_encode_varlen(0))
    track_bytes.extend(b'\xFF\x51\x03')
    track_bytes.extend(struct.pack('>I', microseconds_per_beat)[1:])

    # Program change: channel 0 acoustic piano
    track_bytes.extend(_encode_varlen(0))
    track_bytes.extend(b'\xC0\x00')

    # Add notes
    for n in notes:
        midi_pitch = int(n.get("midi", 60))
        beats = float(n.get("beats", 1.0))
        dur_ticks = int(beats * ticks_per_beat)

        # Note On: delta=0, 0x90, pitch, velocity=95
        track_bytes.extend(_encode_varlen(0))
        track_bytes.extend(bytes([0x90, midi_pitch & 0x7F, 95]))

        # Note Off: delta=dur_ticks, 0x80, pitch, velocity=0
        track_bytes.extend(_encode_varlen(dur_ticks))
        track_bytes.extend(bytes([0x80, midi_pitch & 0x7F, 0]))

    # End of track: delta=0, 0xFF 0x2F 0x00
    track_bytes.extend(_encode_varlen(0))
    track_bytes.extend(b'\xFF\x2F\x00')

    header = struct.pack('>4sIHHH', b'MThd', 6, 1, 1, ticks_per_beat)
    track_header = struct.pack('>4sI', b'MTrk', len(track_bytes))

    return header + track_header + bytes(track_bytes)


def export_midi(psalm_data: Dict[str, Any]) -> bytes:
    """Generates standard MIDI file binary bytes for melody + accompaniment."""
    if MIDO_AVAILABLE:
        try:
            mid = MidiFile()
            tempo_bpm = int(psalm_data.get("tempo", 100))
            microseconds_per_beat = int(60000000 / tempo_bpm)
            ticks_per_beat = 480
            mid.ticks_per_beat = ticks_per_beat

            # Track 0: Melody
            melody_track = MidiTrack()
            mid.tracks.append(melody_track)
            melody_track.append(mido.MetaMessage('set_tempo', tempo=microseconds_per_beat, time=0))
            melody_track.append(mido.MetaMessage('track_name', name='Top Melody', time=0))
            melody_track.append(Message('program_change', program=0, channel=0, time=0))

            notes = psalm_data.get("response", {}).get("notes", [])
            for n in notes:
                midi_pitch = int(n.get("midi", 60))
                beats = float(n.get("beats", 1.0))
                dur_ticks = int(beats * ticks_per_beat)

                melody_track.append(Message('note_on', note=midi_pitch, velocity=95, channel=0, time=0))
                melody_track.append(Message('note_off', note=midi_pitch, velocity=0, channel=0, time=dur_ticks))

            buffer = io.BytesIO()
            mid.save(file=buffer)
            res = buffer.getvalue()
            if len(res) > 0:
                return res
        except Exception:
            pass

    return build_pure_python_midi(psalm_data)
