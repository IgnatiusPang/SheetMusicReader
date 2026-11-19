# Psalm Sheet Music Reader & Realistic Piano Player

A Python web application for church choir singers to view, parse, play, digitize, and practice Psalm sheet music with realistic piano audio, top melody playback, backing accompaniment toggling, 61-key visualizer, score notation with lyrics overlaid directly underneath note heads, full verse support, and score exports (MusicXML, MIDI, JSON).

---

## 🎵 Features

- **20 Pre-Digitized Psalm Sheet Music PDFs**: Parsed and digitized from [data/input/psalms/](data/input/psalms/) into standardized `.json`, `.musicxml`, and `.mid` files in [data/output/digitized_scores/](data/output/digitized_scores/).
- **Lyrics Overlaid Directly Underneath Notes**: Music staves render melody notes with corresponding lyric syllables placed directly underneath note heads, highlighting in real-time as audio plays.
- **Full Verse & Refrain Support**: Seamlessly switch between the **Response Refrain** and all **Verses** (Verse 1, Verse 2, Verse 3, Verse 4) via interactive tab selectors.
- **Realistic Piano & Vocal Guide Audio Engine**: High-fidelity Web Audio API synthesizer with sustained Vocal Guide sing-along tone (for non-pianists), beat clicks, accompaniment chord toggling, wide tempo range (15–200 BPM), speed presets (`100%`, `75%`, `50%`, `33%`, `25%`), and pitch transposition (-4 to +4 semitones).
- **Interactive 61-Key Piano Visualizer**: Real-time piano keyboard lighting up corresponding keys (`C2` to `C7`) during playback or manual key clicks.
- **Live Search & Filtering**: Instantly search Psalms by number (e.g. `103`, `128`, `34`, `109`) or lyric title.
- **Score & Practice Export Options**: Export any Psalm score to:
  - 🎼 **MusicXML** (compatible with MuseScore, Finale, Sibelius, scaled by active speed/augment)
  - 📜 **GNU LilyPond (`.ly`)** (clean engraved score with `\layout {}` and `\midi {}`)
  - 🎹 **MIDI** (compatible with DAWs like GarageBand, Logic Pro, Ableton)
  - 🔊 **Sing-Along WAV** (`vocal_guide` melody + optional chord backing + 1-bar count-in + beat clicks)
  - 💾 **JSON** (standardized digitized score format)
- **Lean 4 Mathematical Verification**: Machine-checked bar-beat conservation and cross-format equivalence (`Original <-> MusicXML <-> LilyPond <-> MIDI <-> Slowed Editions`) backed by `formalization/lean/` and `GET /api/psalms/<id>/verify`.
- **PDF Upload & Automated Digitization**: Upload new Psalm PDF sheet music files to automatically extract titles, keys, time signatures, tempos, chords, melody notes, and lyrics (with `vector_omr.py` support).

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
python -m sheet_music_reader.web.app
```

Open your browser and navigate to:
👉 **[http://localhost:5050](http://localhost:5050)**

*(Note: Default port is set to **5050** to avoid macOS AirPlay Receiver port 5000 conflicts).*

---

## 🛠️ Additional Commands & Batch Utilities

### Batch Digitize All PDF Sheets in `data/input/psalms/`
To parse and convert all PDF files in the `data/input/psalms/` folder into digitized `.json`, `.musicxml`, and `.mid` scores:
```bash
python -m sheet_music_reader.cli.digitize_all
```
*Alternatively, click the **⚡ Digitize All PDFs** button in the top navigation header of the web app.*

### Load & Digitize a Single PDF Sheet Music File
```bash
python -m sheet_music_reader.cli.load_psalm path/to/your_psalm.pdf
```

---

## 🎼 Convert Score PDFs to MIDI (`vector_omr.py`)

Reads PDFs exported from Sibelius, MuseScore 2/3/4 or Finale-style software glyph by glyph (no image guessing for pitches) and writes one MIDI file per PDF, plus an optional LilyPond proof and a bar-by-bar check report.

```bash
python -m sheet_music_reader.omr.vector_omr convert data/input/psalms/*.pdf \
    --out data/output/digitized_scores/vector_midi \
    --proof data/output/digitized_scores/vector_proofs \
    --report data/output/digitized_scores/vector_midi/report.json
```

- Needs `pdftoppm` (poppler) and Python packages numpy, pdfplumber, Pillow, mido; LilyPond only for `--proof`.
- Each output line reports `full` (bars that add up), `edge-short` (pickup/closing bars) and `suspect` (bars to inspect).
- Step-by-step workflow and fixes: `.claude/skills/pdf-to-midi/SKILL.md`. Tests: `pytest tests/test_vector_omr.py`.
- Photos or scans are not vector PDFs; use `omr_pointcloud.py` and the procedure in `notes/session_handover_20261022_2330.md`.

---

## 🎤 Sing-Along Practice, LilyPond Slowdowns & Lean 4 Verification (`music_pipeline.py`)

Convert any PDF, image, MusicXML, LilyPond, or Psalm JSON file into synchronized MusicXML, GNU LilyPond (`.ly`/`.pdf`), MIDI, and sustained **Vocal Guide** audio (`.wav`/`.mp3`) at arbitrary speeds or doubled note values, verified by Lean 4:

```bash
# Convert at 100%, 50%, and 25% speed with printable LilyPond PDF + MP3 + Lean 4 certificate:
python3 -m sheet_music_reader.cli.music_pipeline convert data/input/psalms/03_Ps104103-Lord-Send-Out-Your-Spirit-Chart.pdf \
    --out-dir data/output/practice/verified_practice \
    --speeds 1.0,0.5,0.25 \
    --voice vocal_guide \
    --render-pdf --mp3 --lean-cert

# Generate and immediately play a 50% speed Vocal Guide singing track:
python3 -m sheet_music_reader.cli.music_pipeline sing data/input/psalms/03_Ps104103-Lord-Send-Out-Your-Spirit-Chart.pdf \
    --speed 0.5 --count-in 1 --play

# Build & run Lean 4 theorems and kernel verifier directly:
cd formalization/lean && lake build && ./.lake/build/bin/test_runner
```

---

## 🧪 Running Automated Tests

Run the complete suite of PDF extraction, REST API, OMR, MuseScore helper, Lean 4 formal verification, pipeline synthesis, and Playwright E2E tests:

```bash
python -m pytest
```

---

## 📁 Project Structure

```
SheetMusicReader/
├── sheet_music_reader/         # ALL Python code (one importable package)
│   ├── paths.py                # The only module that knows where data lives
│   ├── psalms_db.py            # JSON score store
│   ├── omr/                    # Reading scores: vector_omr, omr_pointcloud, score_from_image, pdf_parser
│   ├── export/                 # Writing scores: score_formatter, audio_synth, lean_bridge
│   ├── karaoke/                # extract.py (PDF -> timeline of notes, words, chords), render.py (offline HTML)
│   ├── cli/                    # music_pipeline, digitize_all, load_psalm, benchmark_lilypond
│   └── web/                    # Flask app.py, templates/, static/ (css, js, js/karaoke)
├── data/
│   ├── input/                  # Source material only: psalms/*.pdf, Cantabile/, samples/, benchmark_corpus/
│   └── output/                 # Everything generated: digitized_scores/, sing_along_packs/, benchmark/, practice/
├── tests/                      # pytest + Playwright (conftest.py starts the Flask server)
├── formalization/lean/         # Lean 4 project (`SheetMusic` library, `score_verifier`, `test_runner`)
├── crates/sheet_music_engine/  # Rust engraving engine (builds docs/sheet_music_engine.wasm)
├── docs/                       # Static WebAssembly demo site
├── scripts/                    # Node helper for the wasm engraver
├── notes/                      # How-tos, plans, handovers, engraving specification
├── dist/                       # Packaged skill bundles
├── .claude/skills/, .agents/skills/   # Agent & human skills
├── pyproject.toml              # pytest configuration
├── requirements.txt            # Python dependencies
└── README.md
```

Run every tool as a module from the repo root, for example `python -m sheet_music_reader.cli.music_pipeline --help`.

<!-- APAF Bioinformatics | README.md | Approved | 2026-11-15 -->
