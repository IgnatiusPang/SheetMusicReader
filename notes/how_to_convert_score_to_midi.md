---
author: Ignatius Pang
ai_assist: Claude Code (Claude Opus 5.5)
created: 2026-10-25
purpose: Tutorial — how to turn a sheet-music score into a MIDI file in this project
---

# How to convert a musical score into a MIDI file

This note is for someone picking up the project for the first time. It explains which tool to use, how to run
it, how to tell whether the result is right, and what to do when it is not.

## 0. Decide what kind of score you have

| You have | Tool | Quality |
| --- | --- | --- |
| A PDF exported from notation software (Sibelius, MuseScore, Finale) | `vector_omr.py` (this note) | Exact pitches; rhythms checked bar by bar |
| A photo or scan (JPEG, scanned PDF) | `score_from_image.py`, see `notes/how_to_convert_image_to_score_pdf.md` | Automatic: PDF + MIDI + review sheet; 100% pitches on the cantabile photo |

To check which one a PDF is:

```
pdffonts data/<file>.pdf
```

A **vector** score embeds a music font. Look for `Leland` or `Bravura` (MuseScore 3/4), `MScore` (MuseScore 2),
`Opus` (Sibelius), or a font named `TTE…` (Finale via PostScript). If no music font is listed, the PDF is a
picture of a page and `vector_omr.py` cannot read it.

## 1. Set up

- Python: use `/Users/ignatiuspang/anaconda3/bin/python`. It has numpy, scipy, scikit-image, pdfplumber, Pillow
  and mido. The Homebrew `python3` does not.
- poppler (`pdftoppm`, `pdffonts`) for page renders.
- LilyPond 2.26 (`brew install lilypond`), only needed for the proof PDFs.

## 2. Convert

```
/Users/ignatiuspang/anaconda3/bin/python vector_omr.py convert data/*.pdf \
    --out digitized_scores/vector_midi \
    --proof digitized_scores/vector_proofs \
    --report digitized_scores/vector_midi/report.json
```

| Option | Meaning |
| --- | --- |
| `--out` | Folder for one `.mid` per PDF |
| `--proof` | Folder for a re-engraved LilyPond `.ly` and `.pdf` of what was read |
| `--report` | JSON with per-file bar counts, suspect bars, sections and playback order |
| `--as-written` | Play the page once top to bottom, without the psalm response/verse arrangement |

Two lines per file are printed, for example (Psalm 80):

```
03_Ps-8079-Lord-Make-Us-Turn-To-You.pdf  sys= 7 staves= 7 bars= 28 notes=114 key=-2 time=[2, 2] q=76 full=28 edge-short=0 suspect=0
                                         play: R V1 R V2 R V3 R*  pickup=2
```

`key` counts sharps (+) or flats (−), `q` is quarter notes per minute, and `R*` is the final response.

A file that fails does not stop the batch; its error is printed and the rest carry on.

## 3. Check the result (do not skip)

1. **Read the report line.**
   - `full` = bars whose notes add up exactly to the time signature.
   - `edge-short` = short bars at the start or end of a line. These are normally pickups and closing bars.
   - `suspect` = any other bar that does not add up. **Every suspect bar must be looked at.** The JSON lists them as
     `sysN staffM barK: got/expected`.
2. **Check the structure.** `play:` should read `R V1 R V2 … R*` for a psalm. `play: all` means no verse labels were
   found (see section 6).
3. **Compare the proof with the original.** Open `digitized_scores/vector_proofs/<name>.pdf` next to the source PDF.
   Boxed `R` / `V1` marks show where each section was detected to start.
4. **Listen** to the `.mid` while following the printed score.

## 4. How the reader works (so you can fix it)

The key idea: a notation-software PDF is not an image. Every notehead, rest, clef and accidental is a character
in a music font, at an exact position. So most of the score can be read as data, and the page image is only
needed for thin strokes that are drawn as lines.

| Step | What is read | Where in `vector_omr.py` |
| --- | --- | --- |
| Glyphs | Each music-font character mapped to a role (notehead, rest, clef, accidental, dot, flag…) | `SMUFL`, `SONATA`, `MSCORE` tables; `glyph_role` |
| Staves | 5 equally spaced horizontal lines; systems = staves joined by a left vertical | `find_staves`, `group_systems` |
| Pitch | Glyph baseline height above the bottom staff line, in half-spaces, plus clef offset, key signature and accidentals | `read_staff`, `diatonic_to_midi`, `key_alter` |
| Note length | Head type (whole/half/black), halved per beam or flag, plus dots | `stem_and_beams` on a 288 dpi render, `n_dots` |
| Tuplets | Small digits 2–6 over a group (2 → ×1.5, 3 → ×2/3) | `tuplet_glyphs`, `apply_tuplets` |
| Bars | Vertical lines that are not stems | `read_staff` |
| Validation and repair | Each bar summed against the time signature; over-full bars fall back to the upper voice, then to a triplet search | `repair`, `triplets`, `report_of` |
| Ties | Thin arcs between same-pitch notes on the render | `mark_ties`, `arc_fraction` |
| Tempo | Digits after "=" times the beat-unit glyph | `tempo_of` |
| MIDI | Track 1 = top staff (melody); further tracks follow staff order; tied notes merged | `lane_notes`, `write_midi` |

The bar-sum check is the main correctness signal. If every bar adds up and the proof looks like the original,
the MIDI is right.

## 5. Psalm structure: response and verses

Responsorial psalms are printed as a response (refrain) followed by verses. They are sung
R, V1, R, V2, …, Vn, R, so the MIDI is arranged that way by default.

- **Verse starts** are found from labels: `VERSE n`, `Verse n`, `Vs. n`, `V.n`, boxed numbers, or `n.` at the
  start of a lyric line. Each label is attached to the staff it sits beside (`page_labels`, `assign_label`).
- **The response** is everything before the first verse, or what follows a `Response`/`Refrain` label.
  A printed `Final`/`Coda` section replaces the last response.
- **Stacked verses**: when verses 1–4 are printed as separate staves in one system (Psalm 106), each verse uses
  its own staff (`sections_of`).
- **Verse pickup**: the response often ends with the first note or two of the verse (Psalm 80: D, F). These are
  found automatically in two ways (`tail_pickup`):
  - `extra` — Sibelius prints them with special noteheads outside the bar count.
  - `inbar` — notes after the last rest of the response's final bar, when the first verse bar is already complete.

  The pickup plays before every verse and is silenced in the final response, so the piece ends on the response's
  last note.

## 6. When something is wrong

| Symptom | Likely cause | Fix in |
| --- | --- | --- |
| Notes missing entirely | Font code not in the glyph table | `SMUFL` / `SONATA` / `MSCORE`; list unknown codes with pdfplumber `page.chars` per font |
| Eighths read as quarters | Stem or beam not found | `stem_and_beams` |
| Bar 1.5× too short in 6/8 | Duplet "2" missed | `tuplet_glyphs` |
| Bar over-full by one note value | Triplet "3" missed | `tuplet_glyphs`, fallback `triplets` |
| Extra dot on a note or rest | Repeat-sign dots counted | `n_dots`, `repeat_col` |
| Lower staves in the wrong metre | Time signature printed once only | score-wide `"time"` state in `read_score` |
| Absurd tempo | Neighbouring digits picked up | `tempo_of` |
| `play: all` | Verse labels not found or not attached | `page_labels`, `assign_label` |
| Pickup missing before verses | Pickup in an unmapped glyph, or no rest before it | glyph tables, `tail_pickup` |

To look at one bar's events:

```python
from pathlib import Path
import vector_omr as v
sc = v.read_score(Path("data/X.pdf"))
m = sc.systems[S][0].measures[B]          # system S, top staff, bar B
print(list(map(lambda e: (round(e.x), e.midis, e.value, e.stem), m.events)))
```

To see a bar of the original close up: `pdftoppm -r 300 -png -f 1 -l 1 -x X -y Y -W W -H H data/X.pdf crop`.

After any code change, rerun **all** PDFs and confirm no file got worse, then run the tests:

```
/Users/ignatiuspang/anaconda3/bin/python -m pytest tests/test_vector_omr.py
```

Project rule: no imperative `for` loops; use `map`, `filter`, `reduce` or numpy vectorisation.

## 7. Known limits

- Repeat signs and first/second endings inside a section are played once (Psalm 1's response is not doubled).
- The "(8)" under a tenor clef is not read, so such staves sound an octave high (Psalm 96, accompaniment only).
- Chord symbols and lyrics are not converted. Cue-size notes are skipped.
- When two voices share a staff and the bar overflows, only the upper voice is kept.
- The app still plays the older `digitized_scores/<id>.mid` files; the new files in `digitized_scores/vector_midi/`
  are not yet wired in.

## Further reading

- `.claude/skills/pdf-to-midi/SKILL.md` — the same workflow in short form for Claude Code.
- `notes/session_handover_20261025_2140.md` — how the tool was built and the results on all 17 psalm PDFs.
- `notes/session_handover_20261022_2330.md` — the photo/scan route (`omr_pointcloud.py`).

<!-- APAF Bioinformatics | R_is_for_Robot | Approved -->
