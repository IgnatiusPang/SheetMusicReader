#!/usr/bin/env python3
"""
Batch Digitizer for Psalm Sheet Music PDF Files in data/
Digitzes all PDFs into standardized JSON, MusicXML, and MIDI files in digitized_scores/
"""

import os
import glob
import json
import pdf_parser
import psalms_db
import score_formatter

def digitize_all_psalms(data_dir: str = None, force: bool = True):
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")

    scores_dir = psalms_db.SCORES_DIR
    os.makedirs(scores_dir, exist_ok=True)

    pdf_files = sorted(glob.glob(os.path.join(data_dir, "*.pdf")))
    print(f"🎵 Found {len(pdf_files)} Psalm PDF files to digitize in '{data_dir}'...\n")

    digitized_records = []

    for i, pdf_path in enumerate(pdf_files, 1):
        fname = os.path.basename(pdf_path)
        print(f"[{i:02d}/{len(pdf_files)}] Parsing and digitizing: {fname}...")
        
        score_data = pdf_parser.parse_pdf_psalm(pdf_path)
        psalm_id = score_data["id"]
        
        # Save JSON score
        json_path = os.path.join(scores_dir, f"{psalm_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(score_data, f, indent=2)

        # Generate & save MusicXML
        xml_content = score_formatter.export_musicxml(score_data)
        xml_path = os.path.join(scores_dir, f"{psalm_id}.musicxml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        # Generate & save MIDI
        midi_bytes = score_formatter.export_midi(score_data)
        if midi_bytes:
            midi_path = os.path.join(scores_dir, f"{psalm_id}.mid")
            with open(midi_path, "wb") as f:
                f.write(midi_bytes)

        digitized_records.append(score_data)
        print(f"     -> Title: {score_data['title']} | Key: {score_data['key']} | Time: {score_data['time_signature']}")

    print(f"\n✅ Successfully digitized all {len(digitized_records)} Psalms into '{scores_dir}'!")
    return digitized_records

if __name__ == "__main__":
    digitize_all_psalms()
