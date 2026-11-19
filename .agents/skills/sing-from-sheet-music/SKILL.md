---
name: sing-from-sheet-music
description: >-
  Learn to sing a song directly from PDF, scanned image, MusicXML, or LilyPond sheet
  music without knowing how to play piano. Converts notation into slowed GNU LilyPond
  and MuseScore files plus a clear Vocal Guide audio track (.wav/.mp3) with 1-bar
  count-in, beat clicks, and optional soft chord backing.
---

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-11-15 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

# Sing Along From Sheet Music (No Piano Required)

Use this skill when you want to **learn and sing a melody straight from sheet music** (PDF, phone photo, MusicXML, or LilyPond) at comfortable practice speeds without playing an instrument (see `references.md` items 24, 26, and 27).

---

## What You Get

1. **Vocal Guide Melody Audio (`.wav` / optional `.mp3`)**: Uses a smooth, sustained vowel-like lead tone (`vocal_guide`) that holds the exact pitch for the entire note duration so your voice can lock onto every note and rhythm clearly.
2. **Built-In Count-In & Beat Clicks**: Starts with a 1-bar accented woodblock count-in and optional beat clicks so you know exactly when to breathe and enter—even at half speed (`50%`) or quarter speed (`25%`).
3. **Printable Slow Sheet Music (`.ly`, `.pdf`, `.musicxml`)**: Simultaneously produces readable GNU LilyPond and MuseScore scores scaled to your chosen tempo or doubled written note values (`--augment 2`).

---

## Quick Terminal Practice Generation

```bash
# Generate and immediately play a 50% speed Vocal Guide track with 1-bar count-in:
python3 music_pipeline.py sing path/to/song.pdf \
    --out-dir output/sing_practice \
    --speed 0.5 \
    --voice vocal_guide \
    --count-in 1 \
    --play

# Build a complete graduated singing ladder (100%, 75%, 50%, 33%, 25%) + MP3 + printable LilyPond PDF + Lean 4 check:
python3 music_pipeline.py convert path/to/song.pdf \
    --out-dir output/sing_ladder \
    --speeds 1.0,0.75,0.5,1/3,0.25 \
    --voice vocal_guide \
    --render-pdf \
    --mp3 \
    --lean-cert

# Practice reading halved note speed + visually doubled note values (e.g., quarter notes shown as half notes):
python3 music_pipeline.py convert path/to/song.pdf \
    --out-dir output/augmented \
    --speed 0.5 \
    --augment 2 \
    --voice vocal_guide
```

---

## Using the Interactive Web Player (port `5050`)

1. Start the app (`python3 app.py`) and select or upload your PDF score.
2. Keep **Vocal Guide (Sing-Along)** switched ON for sustained pitch-matching playback (switch it off to hear percussive piano).
3. Turn ON **Beat Click** if you want live beat clicks during practice.
4. Click a speed preset (**`100%`**, **`75%`**, **`50%`**, **`33%`**, **`25%`**) or drag the tempo slider all the way down to `15` BPM.
5. Click **🔊 Sing WAV** to download the current slow practice track with count-in for listening offline on your phone, or **📜 LilyPond** / **🎼 MusicXML** to print or inspect the slowed score.

<!-- APAF Bioinformatics | SKILL.md | Approved | 2026-11-15 -->
