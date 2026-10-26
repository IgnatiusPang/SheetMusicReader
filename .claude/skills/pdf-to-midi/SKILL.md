---
name: pdf-to-midi
description: Convert sheet-music PDFs exported from notation software (Sibelius, MuseScore, Finale-style) into MIDI files with vector_omr.py, check the bar-sum report and LilyPond proofs, and fix misreads. Use when the user asks to turn a score PDF into MIDI, audio playback, or a playable file. Not for photos or scans; for those see notes/session_handover_20261022_2330.md (omr_pointcloud.py).
---

# PDF → MIDI with vector_omr.py

## 1. Check the PDF is vector music
```
pdfinfo <file.pdf> | grep -E "Creator|Producer"
pdffonts <file.pdf>
```
A music font must be embedded: Leland/Bravura (MuseScore 3/4), MScore (MuseScore 2), Opus (Sibelius), or a `TTE…` TrueType font holding Maestro/Sonata glyphs (Finale via PostScript). No music font means a scan or photo, which this tool cannot read.

## 2. Convert
Use the anaconda interpreter, which has numpy, pdfplumber, Pillow and mido. LilyPond is needed only for proofs.
```
/Users/ignatiuspang/anaconda3/bin/python vector_omr.py convert data/*.pdf \
    --out digitized_scores/vector_midi --proof digitized_scores/vector_proofs \
    --report digitized_scores/vector_midi/report.json
```
Output: one `.mid` per PDF. Track 1 is the top staff of each system (the melody). Further tracks follow staff order within the system. Ties are merged and tempo comes from the metronome mark (default 90 quarter beats per minute).

## 3. Psalm structure (response / verses)
By default the MIDI plays **R, V1, R, V2, …, Vn, R**: each verse is followed by the response, and a printed "Final" section replaces the last response. Detection:
- Verse starts: `VERSE n`, `Verse n`, `Vs. n`, `V.n`, boxed numbers, or `n.` at the start of a lyric line, each attached to the staff it introduces. Footer text is ignored because it is far from any staff.
- Response = systems before the first verse, or from a `Response`/`Refrain` label.
- Stacked verse staves in one system (e.g. Psalm 106) give one verse per labelled staff.
- Verse pickup at the end of the response: Sibelius special noteheads outside the bar count, or notes after the last rest of the final response bar when the first verse bar is complete. It plays before every verse and is silenced in the final response.
The report shows `sections` (e.g. `R[s1] V1[s2,s3]`), `playback` and `pickup_notes`; proofs carry boxed R / V1 marks at section starts. Use `--as-written` to play the page once top to bottom.

## 4. Read the report line
`full` = bars whose notes add up to the time signature. `edge-short` = short bars at the start or end of a line (pickups and closing bars, normally correct). `suspect` = short or over-full bars elsewhere. Every suspect bar needs a look, and the JSON report lists each one as `sysN staffM barK: got/expected`.

## 5. Inspect suspects
Open the proof PDF (bars that do not add up carry a `%{ got/expected %}` comment in the `.ly`). Compare it with the original rendered at 70–90 dpi (`pdftoppm -r 80 -png -f 1 -l 1`). Crop a bar at 300 dpi with `-x -y -W -H` when a detail matters. Print a bar's events:
```python
from pathlib import Path; import vector_omr as v
sc = v.read_score(Path("data/X.pdf")); m = sc.systems[S][0].measures[B]
print(list(map(lambda e: (round(e.x), e.midis, e.value, e.stem), m.events)))
```

## 6. Known failure modes and where to fix them
| Symptom | Cause | Fix location |
| --- | --- | --- |
| Unknown glyphs, notes missing | font table lacks a code | `SMUFL` / `SONATA` / `MSCORE`; census with `pdfplumber` chars per font |
| Eighths read as quarters | stem not found (thin stem, short beamed stem, wide side bearing) | `stem_and_beams` |
| Bar 1.5x too short in 6/8 | duplet "2" not detected | `tuplet_glyphs` (isolation rule, font) |
| Bar over-full by one note value | triplet "3" missing | `tuplet_glyphs`, fallback `triplets` |
| Extra dot | repeat-sign dots beside a rest or note | `n_dots` / `repeat_col` |
| Wrong metre on lower staves | time signature printed only once | score-wide `"time"` state in `read_score` |
| Absurd tempo | digits from neighbouring text | `tempo_of` |
| Plays straight through (`play: all`) | verse labels not found or not attached | `page_labels`, `assign_label` (print `v.page_labels(page, 0)` and staff tops) |
| Pickup missing before verses | pickup notes in an unmapped glyph, or no rest before them | glyph tables, `tail_pickup` |

After any change, rerun all PDFs and confirm no file regressed, then run `pytest tests/test_vector_omr.py`.

## Limits
Repeat signs and first/second endings inside a section are played once as written (a repeated response is not doubled). The "(8)" under a tenor clef is not read, so such staves sound an octave high. Chord symbols and lyrics are not converted. Cue-size notes are skipped. On a staff with two voices only the upper voice is kept when the bar overflows.

<!-- APAF Bioinformatics | SKILL.md | Approved | 2026-10-25 -->
