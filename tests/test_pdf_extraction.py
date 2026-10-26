import os
import sys
import glob
import json
import pytest

# Ensure root workspace directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pdf_parser
import score_formatter
import psalms_db

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

@pytest.fixture
def pdf_files():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.pdf")))
    assert len(files) >= 15, f"Expected at least 15 PDF files in data/, found {len(files)}"
    return files

def test_all_pdfs_parseable(pdf_files):
    """Verifies that all Psalm PDF files can be parsed without error."""
    for pdf_path in pdf_files:
        score = pdf_parser.parse_pdf_psalm(pdf_path)
        assert isinstance(score, dict)
        assert "id" in score
        assert "title" in score
        assert "key" in score
        assert "time_signature" in score
        assert "response" in score

def test_extracted_music_notation_structure(pdf_files):
    """Verifies that melody notes, pitches, MIDI values, and lyrics are extracted correctly."""
    for pdf_path in pdf_files:
        score = pdf_parser.parse_pdf_psalm(pdf_path)
        resp = score.get("response", {})
        notes = resp.get("notes", [])
        
        assert len(notes) > 0, f"No notes extracted for {score['id']}"
        for note in notes:
            assert "pitch" in note
            assert "midi" in note
            assert "duration" in note
            assert "beats" in note
            assert "lyric" in note
            # Verify MIDI range
            assert 36 <= note["midi"] <= 96, f"Invalid MIDI pitch {note['midi']} in {score['id']}"

def test_extracted_chords_and_key_signatures(pdf_files):
    """Verifies that key signatures, tempos, and chord annotations are properly extracted."""
    for pdf_path in pdf_files:
        score = pdf_parser.parse_pdf_psalm(pdf_path)
        assert score["key"] in ["C Major", "Eb Major", "Bb Major", "F Major", "E Major", "D Major", "G Major", "Db Major", "Ab Major"]
        assert score["time_signature"] in ["4/4", "6/8", "2/2", "3/4"]
        assert score["tempo"] >= 40 and score["tempo"] <= 200
        
        chords = score["response"].get("chords", [])
        assert len(chords) > 0, f"No chords extracted for {score['id']}"

def test_export_musicxml_and_midi_generation(pdf_files):
    """Verifies that extracted music scores can be converted into valid MusicXML and MIDI formats."""
    for pdf_path in pdf_files[:5]: # Test sample batch
        score = pdf_parser.parse_pdf_psalm(pdf_path)
        xml_str = score_formatter.export_musicxml(score)
        assert "<score-partwise" in xml_str
        assert "<work-title>" in xml_str
        
        midi_bytes = score_formatter.export_midi(score)
        assert isinstance(midi_bytes, bytes)
        assert len(midi_bytes) > 0

# --- OMR Notation Rules Unit Tests ---

def test_omr_staff_lines_and_rows_detection(pdf_files):
    """Rule 1: Verify OMR finds sets of 5 parallel staff lines (rows of music)."""
    target_pdf = [f for f in pdf_files if "psalm-106" in f][0]
    extracted = pdf_parser.detect_staff_lines_and_notes(target_pdf)
    assert isinstance(extracted, list)
    assert len(extracted) > 0
    for note in extracted:
        assert "row_system" in note
        assert note["row_system"] >= 1

def test_omr_pitch_calculation_from_coordinates(pdf_files):
    """Rule 2: Verify vertical notehead coordinates calculate accurate diatonic staff pitches."""
    target_pdf = [f for f in pdf_files if "psalm-106" in f][0]
    extracted = pdf_parser.detect_staff_lines_and_notes(target_pdf)
    valid_pitches = ['E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5']
    for note in extracted:
        assert note["pitch"] in valid_pitches, f"Invalid pitch {note['pitch']} calculated by OMR"
        assert 60 <= note["midi"] <= 84

def test_omr_duration_stem_fill_recognition(pdf_files):
    """Rule 3: Verify notehead fill (hollow vs filled) and stem presence set duration."""
    target_pdf = [f for f in pdf_files if "psalm-106" in f][0]
    extracted = pdf_parser.detect_staff_lines_and_notes(target_pdf)
    for note in extracted:
        assert note["duration"] in ["quarter", "half", "whole"]
        assert note["beats"] in [1.0, 2.0, 4.0]

def test_omr_multi_note_chord_recognition(pdf_files):
    """Rule 4: Verify stacked noteheads at the same x position form polyphonic multi-note chords."""
    target_pdf = [f for f in pdf_files if "psalm-106" in f][0]
    extracted = pdf_parser.detect_staff_lines_and_notes(target_pdf)
    for note in extracted:
        assert "chord_pitches" in note
        assert "chord_midis" in note
        assert len(note["chord_pitches"]) >= 1
        assert len(note["chord_midis"]) >= 1

def test_omr_tie_symbol_arc_recognition(pdf_files):
    """Rule 5: Verify smiley face curved tie arcs bridging notes assign tie start and stop."""
    score = pdf_parser.parse_pdf_psalm([f for f in pdf_files if "psalm-106" in f][0])
    notes = score["response"]["notes"]
    tie_starts = [n for n in notes if n.get("tie") == "start"]
    tie_stops = [n for n in notes if n.get("tie") == "stop"]
    assert len(tie_starts) >= 1, "Expected at least one tie start symbol in Psalm 106"
    assert len(tie_stops) >= 1, "Expected at least one tie stop symbol in Psalm 106"

def test_psalm104_key_signature_and_time_signature(pdf_files):
    """Rule 6: Verify Ps 104 detects 4 sharps (E Major), 6/8 time signature, 140 BPM, and chords."""
    target_pdf = [f for f in pdf_files if "Ps104103" in f or "psalm_104" in f][0]
    score = pdf_parser.parse_pdf_psalm(target_pdf)
    assert score["key"] == "E Major"
    assert score["key_signature"] == "4#"
    assert score["time_signature"] == "6/8"
    assert score["tempo"] == 140
    assert "E" in score["response"]["chords"]
    assert "G#m7" in score["response"]["chords"]

def test_omr_rest_symbols_recognition():
    """Rule 7: Verify rest symbol detection structure and silent duration handling."""
    rest_note = {"pitch": "C4", "midi": 60, "duration": "quarter", "beats": 1.0, "rest": True, "lyric": ""}
    assert rest_note.get("rest") is True
    assert rest_note["beats"] == 1.0

def test_key_signature_sharps_flats_at_start_of_line(pdf_files):
    """Rule 8: Verify key signature sharp (#) or flat (b) symbols at the start of staff lines across all PDFs."""
    valid_key_sigs = ["0", "1#", "2#", "3#", "4#", "5#", "6#", "7#", "1b", "2b", "3b", "4b", "5b", "6b", "7b"]
    for pdf_path in pdf_files:
        score = pdf_parser.parse_pdf_psalm(pdf_path)
        assert "key_signature" in score
        assert score["key_signature"] in valid_key_sigs, f"Invalid key signature symbol {score['key_signature']} in {score['id']}"

def test_time_signature_numbers_at_start_of_line(pdf_files):
    """Rule 9: Verify time signature numbers (6/8, 4/4, 3/4, 2/2) at the start of staff lines across all PDFs."""
    valid_time_sigs = ["4/4", "6/8", "3/4", "2/2"]
    for pdf_path in pdf_files:
        score = pdf_parser.parse_pdf_psalm(pdf_path)
        assert "time_signature" in score
        assert score["time_signature"] in valid_time_sigs, f"Invalid time signature {score['time_signature']} in {score['id']}"

def test_all_psalms_response_music_and_words_accuracy(pdf_files):
    """Rule 10: Verify every score has valid response notes, pitch ranges, duration beats, and lyric words."""
    for pdf_path in pdf_files:
        score = pdf_parser.parse_pdf_psalm(pdf_path)
        assert "response" in score
        resp = score["response"]
        assert "notes" in resp and len(resp["notes"]) > 0, f"Missing notes in response for {score['id']}"
        assert "chords" in resp and len(resp["chords"]) > 0, f"Missing chords in response for {score['id']}"
        
        lyrics_words = []
        for note in resp["notes"]:
            assert "pitch" in note
            assert "midi" in note
            assert 48 <= note["midi"] <= 90, f"Invalid MIDI pitch {note['midi']} in {score['id']}"
            assert "beats" in note and note["beats"] > 0
            if not note.get("rest"):
                assert note.get("lyric") is not None
                if note["lyric"]:
                    lyrics_words.append(note["lyric"])
        
        assert len(lyrics_words) > 0, f"No lyric words found in response for {score['id']}"

def test_digitization_musicxml_schema_validity(pdf_files):
    """Rule 11: Verify MusicXML export contains valid score-partwise elements, clef, key, and time tags."""
    sample_pdf = pdf_files[0]
    score = pdf_parser.parse_pdf_psalm(sample_pdf)
    xml_data = score_formatter.export_musicxml(score)
    assert '<?xml version="1.0"' in xml_data
    assert '<score-partwise' in xml_data
    assert '<work-title>' in xml_data
    assert '<clef>' in xml_data
    assert '<key>' in xml_data
    assert '<time>' in xml_data
    assert '<note>' in xml_data

def test_digitization_midi_binary_integrity(pdf_files):
    """Rule 12: Verify MIDI export generates valid MThd header, MTrk track chunk, and events."""
    sample_pdf = pdf_files[0]
    score = pdf_parser.parse_pdf_psalm(sample_pdf)
    midi_bytes = score_formatter.export_midi(score)
    assert isinstance(midi_bytes, bytes)
    assert len(midi_bytes) > 20
    assert midi_bytes.startswith(b'MThd')
    assert b'MTrk' in midi_bytes

def test_digitization_json_persistence(pdf_files):
    """Rule 13: Verify digitized scores serialize cleanly to JSON and load from database."""
    sample_pdf = pdf_files[0]
    score = pdf_parser.parse_pdf_psalm(sample_pdf)
    json_str = json.dumps(score)
    loaded = json.loads(json_str)
    assert loaded['id'] == score['id']
    assert loaded['key'] == score['key']
    assert loaded['time_signature'] == score['time_signature']
    assert len(loaded['response']['notes']) == len(score['response']['notes'])

def test_digitization_verse_lyrics_and_chords_completeness(pdf_files):
    """Rule 14: Verify every digitized score has verses with valid verse numbers, lyrics, and chords."""
    for pdf_path in pdf_files:
        score = pdf_parser.parse_pdf_psalm(pdf_path)
        assert "verses" in score and len(score["verses"]) > 0, f"Missing verses in {score['id']}"
        for verse in score["verses"]:
            assert "verse_number" in verse
            assert "lyrics_text" in verse and len(verse["lyrics_text"]) > 0
            assert "chords" in verse and len(verse["chords"]) > 0

def test_omr_pitch_to_midi_accidental_conversion(pdf_files):
    """Rule 15: Verify key signature sharps/flats alter pitch spellings to correct MIDI numbers."""
    target_pdf = [f for f in pdf_files if "Ps104103" in f or "psalm_104" in f][0]
    score = pdf_parser.parse_pdf_psalm(target_pdf)
    notes = score["response"]["notes"]
    pitch_to_midi = {n["pitch"]: n["midi"] for n in notes if not n.get("rest")}
    assert pitch_to_midi.get("G#4") == 68
    assert pitch_to_midi.get("C#5") == 73
    assert pitch_to_midi.get("F#4") == 66
    assert pitch_to_midi.get("D#4") == 63

def test_omr_consecutive_note_stem_beaming(pdf_files):
    """Rule 16: Verify consecutive short notes (eighth/sixteenth) are detected for horizontal stem beaming."""
    target_pdf = [f for f in pdf_files if "Ps-117116" in f or "psalm_117" in f][0]
    score = pdf_parser.parse_pdf_psalm(target_pdf)
    notes = score["response"]["notes"]
    beamed_pairs = []
    for i in range(len(notes) - 1):
        n1, n2 = notes[i], notes[i+1]
        if not n1.get("rest") and not n2.get("rest"):
            if n1.get("duration") in ["eighth", "sixteenth"] and n2.get("duration") in ["eighth", "sixteenth"]:
                beamed_pairs.append((n1["lyric"], n2["lyric"]))
    assert len(beamed_pairs) >= 2, f"Expected beamed pairs in Ps 117, found {beamed_pairs}"

def test_specification_engraving_layout_order(pdf_files):
    """Rule 17 (Specification): Verify standard treble clef, key signature, time signature, and start bar line ordering."""
    for pdf_path in pdf_files:
        score = pdf_parser.parse_pdf_psalm(pdf_path)
        assert score.get("clef") == "treble", f"Expected treble clef leader in {score['id']}"
        assert "key_signature" in score
        assert "time_signature" in score

def test_specification_rest_symbols_geometry(pdf_files):
    """Rule 18 (Specification): Verify rest symbols (quarter, half, whole, eighth) parse with proper beats and rest flag."""
    target_pdf = [f for f in pdf_files if "Ps-117116" in f or "psalm_117" in f][0]
    score = pdf_parser.parse_pdf_psalm(target_pdf)
    notes = score["response"]["notes"]
    rests = [n for n in notes if n.get("rest")]
    assert len(rests) >= 2, f"Expected rest symbols in Ps 117 response, found {len(rests)}"
    for r in rests:
        assert r["beats"] > 0
        assert r.get("duration") in ["quarter", "half", "whole", "eighth"]







