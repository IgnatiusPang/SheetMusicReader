---
name: slow-practice-musescore
description: >-
  Take an existing MusicXML (.musicxml) score for violin or piano, double-check
  that its bars and tempos are valid, and generate slow and ultra-slow practice
  files (half speed 50%, one-third speed 33%, quarter speed 25%, or custom BPM)
  with optional 8th-note subdivision clicks and hands-separate piano parts.
---

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-11-15 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

# Slow & Ultra-Slow Practice Pack for MuseScore (Violin & Piano)

Use this skill when you already have a translated **MusicXML (`.musicxml`)** score and want to create slow practice versions for a violin or piano student—not just half speed (`50%`), but much slower speeds (`33%`, `25%`, `20%`, or exact metronome markings like `♩ = 30`), with a double-check step to confirm that every note and rhythm stayed intact.

> Need to convert a PDF or photo into MusicXML first? Start with the [`pdf-to-musescore`](../pdf-to-musescore/SKILL.md) skill.

---

## Why Make Dedicated Slow Files Instead of Dragging the Slider?

1. **Ready in one click**: Double-clicking `Piece_33pct.musicxml` in MuseScore opens the score with `♩ = 30` already set in both the visible heading and the playback engine. Press **Spacebar** and it plays at one-third speed right away.
2. **Subdivided guide pulse for very slow speeds**: When you slow a piece down to `25%` or `33%` speed, quarter-note beats sit two or three seconds apart. Students easily rush during a half note or dotted quarter note. For speeds at or below `40%`, our helper script automatically adds an **8th-note subdivision click staff** (alternating high/low woodblock on the beat and the `"&"` of the beat) so the student always hears the inner pulse.
3. **Hands-separate files for piano**: With `--hands-separate`, the script also creates `Right Hand Only` and `Left Hand Only` files at every practice speed.
4. **Playable MIDI files included**: Every speed also saves a matching `.mid` file so you can email or text the slow audio track to a parent or student who doesn't have MuseScore at home.

---

## Step 1: Double-Check the Score First (`verify`)

Before generating five different practice speeds, make sure the source `.musicxml` file has no rhythm or pitch errors. Run:

```bash
python3 ../pdf-to-musescore/scripts/musescore_helper.py verify path/to/piece.musicxml --instrument auto
```

*(Pass `--instrument violin` or `--instrument piano` to enforce violin G3 range checks or piano two-hand bar alignment).*

Confirm that the report says:
- `Overall Status : PASS`
- `Suspect: 0` on every part
- No unclosed ties or out-of-range pitch warnings.

If any bar is listed under `Bars Needing Attention`, fix that bar in the source `.musicxml` file before generating the slow pack.

---

## Step 2: Generate the Slow Practice Ladder (`slow`)

### Standard Graduated Practice Ladder (`100%`, `75%`, `50%`, `33%`, `25%`)
This gives a student a step-by-step ladder from ultra-slow note learning (`25%` and `33%`) up through half speed (`50%`), three-quarter speed (`75%`), and full tempo (`100%`):

```bash
# Violin slow practice pack:
python3 ../pdf-to-musescore/scripts/musescore_helper.py slow path/to/piece.musicxml \
    --out path/to/practice_pack \
    --speeds 100%,75%,50%,33%,25% \
    --instrument violin

# Piano slow practice pack (with Right-Hand-only and Left-Hand-only files):
python3 ../pdf-to-musescore/scripts/musescore_helper.py slow path/to/piece.musicxml \
    --out path/to/practice_pack \
    --speeds 100%,75%,50%,33%,25% \
    --instrument piano \
    --hands-separate
```

### Custom Ultra-Slow Speeds or Exact Metronome BPMs
If a student needs an even slower tempo for a difficult passage (for example, `20%` speed or specific metronome markings):

```bash
# By percentage (down to 15% or 20%):
python3 ../pdf-to-musescore/scripts/musescore_helper.py slow path/to/piece.musicxml \
    --speeds 50%,33%,25%,20% \
    --instrument violin

# By exact BPM (e.g., quarter note = 24, 32, 44, 60):
python3 ../pdf-to-musescore/scripts/musescore_helper.py slow path/to/piece.musicxml \
    --bpm 24,32,44,60 \
    --instrument violin
```

### Useful Options

| Flag | What it does |
| :--- | :--- |
| `--speeds 50%,33%,25%` | Choose any combination of speed percentages or ratios (`0.5,0.33,0.25`). |
| `--bpm 30,45,60` | Generate files at exact metronome BPMs instead of percentages. |
| `--base-bpm 88` | Tell the script the original BPM if the PDF didn't have a metronome number printed on it. |
| `--instrument violin` or `piano` | Sets the playback sound in MuseScore and MIDI (`Violin` vs. `Grand Piano`). |
| `--hands-separate` | For 2-part piano scores, also writes `_RH_only.musicxml` and `_LH_only.musicxml` at each speed. |
| `--guide-click` | Force the 8th-note subdivision click track on *all* speeds (by default it is added on speeds `<= 40%`). |
| `--no-auto-click` | Leave out the 8th-note subdivision click track even on ultra-slow speeds. |
| `--export-mscz` | If MuseScore is installed on the computer, also save native `.mscz` files automatically. |
| `--lilypond` | Also emit GNU LilyPond (`.ly`) notation files alongside each slow speed. |
| `--lean-verify` | Run Lean 4 bar-beat and note-parity verification across outputs when available. |

---

## Step 3: Confirm the Post-Generation Double-Check

When `slow` finishes, read the two verification lines printed at the top of its output:

```text
=== Slow Practice Pack Generated (5 speeds, Violin) ===
Source Score Audit : PASS (0 suspect bars)
Note Parity Check  : PASS (100% identical notes across all speeds)
```

Both lines must say `PASS`. This guarantees that every slow edition has the exact same pitches, rhythms, and ties as the verified score, with only the tempo scaled.

*(Need sustained Vocal Guide audio `.wav`/`.mp3` files to learn a melody by singing? See [`sing-from-sheet-music`](../sing-from-sheet-music/SKILL.md). Need mathematical Lean 4 bar-conservation certificates? See [`lean4-music-verification`](../lean4-music-verification/SKILL.md)).*

<!-- APAF Bioinformatics | SKILL.md | Approved | 2026-11-15 -->

