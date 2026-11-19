---
name: pdf-to-musescore
description: >-
  Convert violin and piano PDF sheet music (digital PDFs, scans, or phone photos)
  into verified MusicXML (.musicxml) and MIDI (.mid) files for MuseScore, run a
  mandatory bar-by-bar double-check step, and generate slow and ultra-slow
  practice editions (75%, 50%, 33%, 25% speed or custom BPM). Use whenever the
  user wants to open a PDF score in MuseScore or make slow practice tracks.
---

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-11-15 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

# PDF Sheet Music to MuseScore (Violin & Piano)

This skill guides both you (the teacher) and your AI coding assistant through turning a PDF page of violin or piano sheet music into a clean **MusicXML (`.musicxml`)** file that opens directly in MuseScore (see `references.md` item 26), checking every bar so no wrong notes slip through, and creating ready-to-play slow practice files at **half speed (`50%`)**, **one-third speed (`33%`)**, **quarter speed (`25%`)**, or any speed your student needs.

---

## Why MusicXML (`.musicxml`) Instead of Just MIDI?

If you give MuseScore a plain `.mid` file, MuseScore has to guess the notation from raw key presses:
- It often spells sharps as flats (`F#` becomes `Gb`), which confuses students reading the page.
- It loses violin bowings (`∏` down-bow, `∨` up-bow), fingerings (`0–4` on violin, `1–5` on piano), slurs, and dynamics.
- On piano pieces, it often scrambles which notes belong to the Right Hand versus the Left Hand.

Always produce a **MusicXML (`.musicxml`)** file for MuseScore alongside a **MIDI (`.mid`)** file for quick listening on a phone or tablet.

---

## Step 1: Check What Kind of PDF You Have

Not all PDFs are the same. Some were exported directly from music software (Sibelius, MuseScore, Finale) and hold exact note data inside the file. Others are scans or phone photos of a paper book.

Have the AI run the bundled helper script first:

```bash
python3 scripts/musescore_helper.py inspect path/to/piece.pdf
```

| What `inspect` reports | What it means | How to convert it |
| :--- | :--- | :--- |
| `vector_pdf` | Digital score with an embedded music font (`Leland`, `Bravura`, `Opus`, `Maestro`). | Read the music glyphs directly (`from-repo` / `vector_omr.py`). Pitches are exact. |
| `scanned_pdf` or `image_score` | A paper scan or phone photo of a printed page. | Read with optical music recognition (`from-repo` / `score_from_image.py` or page-by-page transcription), then pay extra attention during Step 3. |

---

## Step 2: Convert the PDF to MusicXML (`.musicxml`)

### Option A: Using the automated converter in this project
Run `from-repo` and tell it whether the piece is for **violin** or **piano**:

```bash
# For a violin piece:
python3 scripts/musescore_helper.py from-repo path/to/violin_piece.pdf \
    --out output/musescore \
    --instrument violin

# For a piano piece:
python3 scripts/musescore_helper.py from-repo path/to/piano_piece.pdf \
    --out output/musescore \
    --instrument piano
```

### Option B: When the AI transcribes or edits a MusicXML file directly
If you are on another computer without the full OMR pipeline, or if the AI is reading a short piece from a high-resolution page image and writing the `.musicxml` file directly, the AI **must** follow these rules:
1. **Render the PDF at 300 DPI** so ledger lines, sharps, flats, dots, and fingerings are crisp.
2. **Transcribe bar by bar**, adding a clear XML comment `<!-- Bar N -->` before each `<measure number="N">`.
3. **Include the instrument sound tag**:
   - **Violin**: `<midi-program>41</midi-program>` so MuseScore plays a sustained violin sound instead of defaulting to piano.
   - **Piano**: Two parts (`P1` Right Hand in Treble Clef, `P2` Left Hand in Bass Clef), both with `<midi-program>1</midi-program>`.
4. **Ignore pencil marks**: Student copies often have penciled fingerings, circled accidentals, or teacher notes. Transcribe only the printed engraving unless asked otherwise.

---

## Step 3: The Double-Checking Step (Never Skip This)

Music recognition tools—and AI assistants—make predictable mistakes. A speck of dust on a scan looks just like a staccato dot or a dot after a quarter note. A missed clef change in the piano Left Hand puts every note two octaves off.

### Part 1: Run the Automated Code Audit (`verify`)
Before giving any file to the teacher or student, the AI **must** run the `verify` command:

```bash
python3 scripts/musescore_helper.py verify output/musescore/piece.musicxml --instrument violin
```

*(Use `--instrument piano` for piano scores).*

What `verify` checks automatically in code:
1. **Bar-by-Bar Rhythm Math**: Adds up the notes and rests in every bar and checks them against the time signature (`4/4`, `3/4`, `6/8`, etc.).
   - Short first or last bars are marked as `PICKUP` or `CLOSING` (normal).
   - Any interior bar that does not add up is flagged as **`SUSPECT_SHORT`** or **`SUSPECT_OVER`** with the exact missing or extra beat count (for example, `has 3.5 beats, expected 4 beats (-0.5 beats)` usually means an eighth note was misread as a sixteenth, or a dot was missed on a dotted quarter note).
2. **Violin Open-G3 Floor (`MIDI 55`)**: The lowest note on a violin is the open G string (`G3`, MIDI 55). If any note in a violin part falls below `G3`, `verify` flags it immediately.
3. **Piano Right-Hand / Left-Hand Bar Alignment**: Checks that the Right Hand (`P1`) and Left Hand (`P2`) have the exact same number of bars so the two hands never drift out of sync.
4. **Ties & Tempo Sync**: Checks that every `<tie type="start"/>` closes properly on the same pitch, and that the printed metronome mark (`<per-minute>`) matches the hidden playback speed (`<sound tempo="..."/>`).

> **Rule for the AI Assistant**: If `verify` reports `Overall Status : NEEDS_REVIEW` or lists any `Suspect` bars, **do not stop there**. Inspect those exact bar numbers on the original PDF, fix the durations or pitches in the `.musicxml` file, and run `verify` again until it prints `Overall Status : PASS` with `0` suspect bars.

### Part 2: The 5-Point Visual Check (2 Minutes)
Even when every bar adds up to 4 beats, an `A` can still be misread as a `G`. Check these five things against the PDF (see [violin_and_piano_checklist.md](./references/violin_and_piano_checklist.md) for examples):
1. **Bar 1 Setup**: Count the sharps or flats in the key signature, check the time signature, and check the starting clef.
2. **First and Last Note of Each Line**: Glance down the left and right edges of the page to make sure no bar was skipped at a line break.
3. **Accidentals Inside a Bar**: Remember that a sharp, flat, or natural printed early in a bar stays active for that same note through the rest of the bar.
4. **Instrument-Specific Marks**:
   - **Violin**: Check slurs vs. ties (a slur groups notes into one bow; a tie holds the same note), down-bow (`∏`) and up-bow (`∨`) marks, and fingerings (`0, 1, 2, 3, 4`).
   - **Piano**: Watch for the Left Hand switching from Bass Clef (`𝄢`) to Treble Clef (`𝄞`) mid-piece and back again.
5. **Quick Listen**: Open the `.musicxml` in MuseScore, press **Spacebar**, and follow the original PDF with your finger.

---

## Step 4: Create Slow & Ultra-Slow Practice Files (`slow`)

Instead of opening MuseScore and manually dragging the tempo slider to 50% every time, let the script generate a complete **Slow Practice Pack** with the slower tempos already baked into both the score heading and MuseScore's playback engine.

```bash
# Default practice ladder: 100%, 75%, 50% (half), 33% (one-third), and 25% (quarter speed)
python3 scripts/musescore_helper.py slow output/musescore/piece.musicxml \
    --out output/musescore/practice_pack \
    --speeds 1.0,0.75,0.5,0.33,0.25 \
    --instrument violin
```

### Going Even Slower (Ultra-Slow Practice & Subdivision Clicks)
When a student is first learning shifting on the violin or coordinating both hands on the piano, even half speed (`50%`) is sometimes too fast. You can pass any percentage or exact BPM you want:

```bash
# Custom ultra-slow speeds (e.g. 50%, 35%, 25%, and 20% speed):
python3 scripts/musescore_helper.py slow output/musescore/piece.musicxml \
    --speeds 50%,35%,25%,20% \
    --instrument violin

# Or exact metronome numbers (e.g. quarter note = 30, 40, 50, 60 BPM):
python3 scripts/musescore_helper.py slow output/musescore/piece.musicxml \
    --bpm 30,40,50,60 \
    --instrument piano \
    --hands-separate
```

### Helpful Features Built into `slow`
- **Automatic 8th-Note Guide Click on Very Slow Speeds (`<= 40%`)**: When a piece is slowed down to `33%` or `25%` (say, 22 BPM), quarter-note beats are so far apart that students lose the pulse during half notes and dotted notes. On speeds of `40%` or slower, the script automatically adds a gentle **8th-note subdivision click track** (`Practice Click (8th Subdivisions)`). In MuseScore, you can mute or unmute this click track anytime in the Mixer (**F10**), or turn it off with `--no-auto-click`.
- **Piano Hands-Separate Files (`--hands-separate`)**: For two-staff piano pieces, adding `--hands-separate` automatically saves extra `_RH_only.musicxml` (Right Hand alone) and `_LH_only.musicxml` (Left Hand alone) files at each slow speed.
- **Automatic Note-Parity Verification**: Every time `slow` writes a slower file, it re-reads the notes and verifies that 100% of pitches and note lengths match the verified original.
- **GNU LilyPond & Lean 4 Support**: Pass `--lilypond` to also export clean `.ly` scores alongside `.musicxml` and `.mid`, or `--lean-verify` to check exact bar-beat conservation and cross-format equivalence in the Lean 4 kernel when working inside `SheetMusicReader`. For vocal pitch-matching practice tracks, see the companion [`sing-from-sheet-music`](../sing-from-sheet-music/SKILL.md) skill, and for formal verification details see [`lean4-music-verification`](../lean4-music-verification/SKILL.md).

<!-- APAF Bioinformatics | SKILL.md | Approved | 2026-11-15 -->

