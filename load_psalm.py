#!/usr/bin/env python3
"""
Weekly Psalm Loader for Antigravity & Choir Director
Usage:
    python load_psalm.py path/to/psalm.pdf
    python load_psalm.py --json path/to/psalm.json
"""

import os
import sys
import json
import argparse
import pdf_parser
import psalms_db
import score_formatter

def load_from_pdf(pdf_path: str):
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File '{pdf_path}' not found.")
        sys.exit(1)

    print(f"📖 Parsing Psalm PDF: {pdf_path}...")
    digitized_score = pdf_parser.parse_pdf_psalm(pdf_path)
    psalm_id = psalms_db.save_psalm(digitized_score)
    
    # Generate MusicXML & MIDI digitized formats
    scores_dir = psalms_db.SCORES_DIR
    xml_path = os.path.join(scores_dir, f"{psalm_id}.musicxml")
    midi_path = os.path.join(scores_dir, f"{psalm_id}.mid")

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(score_formatter.export_musicxml(digitized_score))

    midi_bytes = score_formatter.export_midi(digitized_score)
    if midi_bytes:
        with open(midi_path, "wb") as f:
            f.write(midi_bytes)

    print(f"✅ Successfully loaded and digitized Psalm '{digitized_score.get('title')}'!")
    print(f"   • Digitized JSON: {os.path.join(scores_dir, f'{psalm_id}.json')}")
    print(f"   • MusicXML: {xml_path}")
    print(f"   • MIDI: {midi_path}")

def main():
    parser = argparse.ArgumentParser(description="Weekly Psalm Digitizer & Loader")
    parser.add_argument("file", help="Path to PDF sheet music or digitized JSON score")
    args = parser.parse_args()

    if args.file.endswith(".json"):
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        psalm_id = psalms_db.save_psalm(data)
        print(f"✅ Saved digitized score '{data.get('title')}' with ID '{psalm_id}'.")
    else:
        load_from_pdf(args.file)

if __name__ == "__main__":
    main()
