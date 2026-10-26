---
author: Ignatius Pang
ai_assist: Claude Code (Claude Fable 5.1)
created: 2026-10-22
modified: 2026-10-22
purpose: Session handover — SheetMusicReader / Cantabile photo-to-engraving
filename_convention: notes/session_handover_YYYYMMDD_HHMM.md (MANDATORY SUFFIX)
---

# Handover: 2026-10-22 23:30 — Ignatius Pang

## Repository/Project
`~/Workings/2026/SheetMusicReader` (not a git repository)

## Session Summary
Converted the photographed, pencil-annotated violin score `data/cantabile.jpeg` (Dancla, *Cantabile*,
ed. Applebaum, AMEB List A No 1) into a clean engraved PDF. The previous attempt
`data/cantabile_engraved.pdf` carried red Preview stamps on the wrong measures. The score was re-transcribed
from the photo into LilyPond and verified by matching the notehead "point cloud" of the photo against the
noteheads read out of the engraved PDF, system by system.

## Completed
- `digitized_scores/cantabile.ly` — LilyPond 2.26 source (single source of truth).
- `data/cantabile_final.pdf` — clean A4 page, 9 systems, 41 measures, 0 annotations.
- `digitized_scores/cantabile.midi` — MIDI from the same source, ♩ = 88.
- `omr_pointcloud.py` — verifier/review module with three subcommands (`compare`, `stamps`, `crops`).
- `tests/test_omr_pointcloud.py` — 18 unit tests, all passing.
- `CANTABILE_PLAN.md` — plan, measure-by-measure change table (WIP → final).
- LilyPond 2.26.0 installed via Homebrew (`brew install lilypond`).

## How the work was done (repeatable procedure)

### 0. Environment
- Python: use the anaconda interpreter, `/Users/ignatiuspang/anaconda3/bin/python` (3.13). It has
  numpy, scipy, scikit-image, Pillow and pdfplumber. The Homebrew `python3` (3.14/3.15) has none of
  them, which is why the IDE shows import errors on `omr_pointcloud.py`; ignore those.
- Poppler CLI (`pdftoppm`, `pdfinfo`, `pdffonts`) for rendering/inspecting PDFs. LilyPond on PATH.
- Keep scratch images and build output in the session scratchpad, not in the repo.

### 1. Inspect the inputs first
- `pdfinfo` / `pdffonts` on the WIP PDF: Creator "LilyPond 2.26.0", fonts Emmentaler-20/11 → it is a
  LilyPond render, so the fix is to produce a corrected LilyPond source, not to retouch an image.
- No `.ly` source survived from the earlier session (searched the repo and old scratchpads), so the
  score had to be re-transcribed. **Next time save the `.ly` into `digitized_scores/` immediately.**

### 2. Read the reviewer's red marks programmatically
```
python omr_pointcloud.py stamps data/cantabile_engraved.pdf
```
Preview's red marks are PDF `Stamp` annotations. The command lists each stamp with the nearest engraved
notehead (pitch, filled/hollow, dx/dy). dy ≈ +4 pt means "on the notehead"; a stamp 8–15 pt above or
left of a head marks a missing accidental, fingering or slur rather than a wrong pitch.

### 3. Make the photo readable (the hard part)
Problems with the photo and what fixed them:
- **Whole-page deskew failed** (dark page border dominated the projection profile; best angle came out
  0°). Fix: deskew each staff system separately, on a locally thresholded (`threshold_local`, block 51,
  offset 10) crop, maximising the variance of the row-sum profile over −6..+6° in 0.1° steps. Skew
  ranged from +4.8° (top system) to −0.3° (bottom), i.e. the page is curved, not just rotated.
- **Page curvature shifts pitches by up to half a step at the right edge** when staff lines are fitted
  with one straight line. Fix: fit each line from three wide windows, then for every notehead refine
  the five line rows inside a ±40 px column window (`PhotoSystem.local_lines`) and compute the diatonic
  step from the *local* bottom line and spacing. This is what settled m5, m16, m17 and m25.
- **Filled noteheads** = binary image → opening with a 5×1 vertical footprint (removes staff lines) →
  opening with `disk(round(0.3·spacing))` (removes stems, beams, slurs, pencil) → `regionprops`
  filtered by area 0.3–3.2·s², height < 1.7·s, width 0.6–2.3·s, x right of the clef/key/time
  signature, y within ±3.2·s of the staff.
- **Hollow noteheads (minims)** were lost by the vertical opening because the ring's top/bottom arcs are
  thinner than 5 px. Fix: fill holes on the *unopened* binary image, bridge the two half-holes that a
  staff line creates with a 5×1 dilation, keep holes of 0.15–1.4·s² with solidity > 0.85.
- Remaining false positives (fingering digits, "0", letters of *cresc.*/*dim.*, hairpins) show up as
  stray A3/C6/E6 entries; they are obvious in the crops and harmless in the alignment.

### 4. Proof-read with labelled crops
```
python omr_pointcloud.py crops data/cantabile.jpeg /path/to/scratch/crops 3.0
```
Writes `pc_s<N>_L.png` / `pc_s<N>_R.png` (left/right halves of each system, 3× zoom) with every
detected head circled and named (green = filled, magenta = hollow). Read them with the Read tool.
Tips: keep crop width ≤ 2000 px (the viewer downsizes anything wider, and a batch of many large images
hit the "media removed: request limit" cap — send ≤ ~12 images per call). For ambiguous spots render an
8× crop of just that bar (`labelled_crop(system, [], x_frac_a, x_frac_b, 8.0)`).
What the crops decide that pitch alone does not: durations/dots/flags, slurs, fingerings (0 = open
string, a good sanity check: every "0" sat on A4 or E5), bowings (⊓), accidentals, hairpins, text.
Pencil marks are dashed/grey; printed hairpins are solid thin lines.

### 5. Transcribe into LilyPond
- Write `digitized_scores/cantabile.ly` in `\relative`, one measure per line with the bar number in a
  comment, `\break` after bars 5, 10, 14, 18, 22, 27, 32, 37 to mirror the print's 9 systems
  (5,5,4,4,4,5,5,5,4 measures).
- Force fingerings and bows above (`^1`, `^\downbow`) so placement is deterministic; cautionary naturals
  with `c''?`; `\numericTimeSignature` because the print shows 4/4 not C; `\tempo "Andante" 4 = 80-96`.
- Build: `lilypond -dno-point-and-click -o <scratch>/cantabile digitized_scores/cantabile.ly`
  (produces `.pdf` and `.midi`), then copy into `data/` and `digitized_scores/`.

### 6. Verify
```
python omr_pointcloud.py compare data/cantabile.jpeg data/cantabile_final.pdf [clouds.json]
python -m pytest tests/test_omr_pointcloud.py -q
```
`compare` aligns the two per-system pitch sequences with `difflib.SequenceMatcher` (monotone alignment —
exact for an ordered 1-D sequence, so no optimal transport / ManifoldFGW needed). A clean result has only
`insert`/`delete` ops (missed hollow heads, text blobs); any `replace` of a real notehead is a transcription
error. Also render the PDF (`pdftoppm -r 200 -png`) and eyeball 3 systems per image; artefacts seen only
in stacked proof strips and not at 600 dpi are rendering artefacts, not PDF content (checked with
`pdfplumber` object queries).

Gotchas in the PDF reader: Emmentaler glyphs come out as `(cid:N)` and the numbering depends on the
font subset, so noteheads are classified by glyph width (black ≈ 6.5 pt, half ≈ 6.9, whole ≈ 7.5–10 at
a 20 pt staff), and the notehead centre is the glyph origin `page.height − matrix[5]`, not the bbox centre.

## Unresolved
- Changes made in *unmarked* measures to match the print (half-note-pair slurs removed in m4, 8, 26, 28,
  33, 35; hairpins m4/28/33 removed; decrescendo m23–24 and `p` m25 added; second down-bow m23 removed)
  await the user's OK — see `CANTABILE_PLAN.md`.
- `data/cantabile_cleaned.pdf` and `data/cantabile_engraved.pdf` are superseded but not deleted (Rule 1
  asks for a deduplicated library; deletion is the user's call).
- No MusicXML/JSON for the app library yet; LilyPond does not export MusicXML.

## Decisions Made
- Re-engrave with LilyPond from the photo rather than clean the JPEG: pencil marks overlap printed ink,
  and the previous PDF was already a LilyPond render.
- Treat the photo as ground truth, the WIP as the layout reference; keep unmarked measures' pitches and
  rhythms, follow the print for articulation and report every such change.
- Verification via per-system notehead point clouds with monotone alignment; ManifoldFGW judged
  unnecessary (systems are ordered sequences, no tearing/holes, alignment is 1-D).
- All Python written without imperative loops (`map`/`filter`/numpy), per the project coding rules.

## Next Steps
1. Listen to `digitized_scores/cantabile.midi` against the recording (references.md item 7) and confirm.
2. If any veto on the unmarked-measure changes: edit the measure in `cantabile.ly`, rebuild, re-run `compare`.
3. Optionally generate MusicXML (e.g. MuseScore import of the `.ly`/MIDI, or `python-ly`) and a JSON in
   the app's `digitized_scores/` format so the piece plays in the web app.
4. Remove the two superseded cantabile PDFs once the final is accepted.
5. For a new photographed score: set `CANTABILE_BANDS`-style y-ranges for its systems (read them off a
   row-sum profile or a 110 dpi render), then repeat steps 2–6.

## Dependencies or Blockers
None. (LilyPond 2.26.0 via Homebrew; anaconda Python 3.13 with numpy/scipy/scikit-image/Pillow/pdfplumber.)

<!-- APAF Bioinformatics | R_is_for_Robot | Approved -->
