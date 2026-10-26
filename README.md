# Psalm Sheet Music Reader & Realistic Piano Player

A Python web application for church choir singers to view, parse, play, digitize, and practice Psalm sheet music with realistic piano audio, top melody playback, backing accompaniment toggling, 61-key visualizer, score notation with lyrics overlaid directly underneath note heads, full verse support, and score exports (MusicXML, MIDI, JSON).

---

## 🎵 Features

- **20 Pre-Digitized Psalm Sheet Music PDFs**: Parsed and digitized from [data/](data/) into standardized `.json`, `.musicxml`, and `.mid` files in [digitized_scores/](digitized_scores/).
- **Lyrics Overlaid Directly Underneath Notes**: Music staves render melody notes with corresponding lyric syllables placed directly underneath note heads, highlighting in real-time as audio plays.
- **Full Verse & Refrain Support**: Seamlessly switch between the **Response Refrain** and all **Verses** (Verse 1, Verse 2, Verse 3, Verse 4) via interactive tab selectors.
- **Realistic Piano Audio Engine**: High-fidelity Web Audio API synthesizer with harmonic overtone modeling, damper resonance, ADSR envelope, accompaniment chord toggling, tempo adjustment (40–200 BPM), and pitch transposition (-4 to +4 semitones).
- **Interactive 61-Key Piano Visualizer**: Real-time piano keyboard lighting up corresponding keys (`C2` to `C7`) during playback or manual key clicks.
- **Live Search & Filtering**: Instantly search Psalms by number (e.g. `103`, `128`, `34`, `109`) or lyric title.
- **Score Export Options**: Export any Psalm score to:
  - 🎼 **MusicXML** (compatible with MuseScore, Finale, Sibelius)
  - 🎹 **MIDI** (compatible with DAWs like GarageBand, Logic Pro, Ableton)
  - 💾 **JSON** (standardized digitized score format)
- **PDF Upload & Automated Digitization**: Upload new Psalm PDF sheet music files to automatically extract titles, keys, time signatures, tempos, chords, melody notes, and lyrics.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Optional for browser testing)*:
```bash
playwright install chromium
```

### 2. Run the Web Application
```bash
python app.py
```

Open your browser and navigate to:
👉 **[http://localhost:5050](http://localhost:5050)**

*(Note: Default port is set to **5050** to avoid macOS AirPlay Receiver port 5000 conflicts).*

---

## 🛠️ Additional Commands & Batch Utilities

### Batch Digitize All PDF Sheets in `data/`
To parse and convert all PDF files in the `data/` folder into digitized `.json`, `.musicxml`, and `.mid` scores:
```bash
python digitize_all.py
```
*Alternatively, click the **⚡ Digitize All PDFs** button in the top navigation header of the web app.*

### Load & Digitize a Single PDF Sheet Music File
```bash
python load_psalm.py path/to/your_psalm.pdf
```

---

## 🎼 Convert Score PDFs to MIDI (`vector_omr.py`)

Reads PDFs exported from Sibelius, MuseScore 2/3/4 or Finale-style software glyph by glyph (no image guessing for pitches) and writes one MIDI file per PDF, plus an optional LilyPond proof and a bar-by-bar check report.

```bash
python vector_omr.py convert data/*.pdf \
    --out digitized_scores/vector_midi \
    --proof digitized_scores/vector_proofs \
    --report digitized_scores/vector_midi/report.json
```

- Needs `pdftoppm` (poppler) and Python packages numpy, pdfplumber, Pillow, mido; LilyPond only for `--proof`.
- Each output line reports `full` (bars that add up), `edge-short` (pickup/closing bars) and `suspect` (bars to inspect).
- Step-by-step workflow and fixes: `.claude/skills/pdf-to-midi/SKILL.md`. Tests: `pytest tests/test_vector_omr.py`.
- Photos or scans are not vector PDFs; use `omr_pointcloud.py` and the procedure in `notes/session_handover_20261022_2330.md`.

---

## 🧪 Running Automated Tests

Run the complete suite of PDF music extraction tests, REST API tests, and Playwright end-to-end browser tests:

```bash
pytest tests/test_pdf_extraction.py tests/test_flask_routes.py tests/test_app.py -v
```

---

## 📁 Project Structure

```
SheetMusicReader/
├── app.py                      # Flask REST API & Web Server
├── pdf_parser.py               # Music extraction software & PDF parser
├── score_formatter.py          # MusicXML & MIDI generator
├── psalms_db.py                # Digitized score manager
├── digitize_all.py             # Batch PDF digitizer runner
├── load_psalm.py               # CLI tool for single PDF loading
├── data/                       # Source Psalm PDF sheet music files
├── digitized_scores/           # Digitized JSON, MusicXML, and MIDI files
├── templates/
│   └── index.html              # Modern glassmorphic Web UI
├── static/
│   ├── css/style.css           # Styling & animation system
│   └── js/
│       ├── piano_synth.js      # Web Audio API realistic piano synthesizer
│       └── app.js              # Application controller & score renderer
├── tests/
│   ├── test_pdf_extraction.py  # Unit tests for PDF music parsing
│   ├── test_flask_routes.py    # Unit tests for REST API endpoints
│   └── test_app.py             # Playwright E2E browser tests
├── requirements.txt            # Python dependencies
└── README.md                   # Application documentation
```
