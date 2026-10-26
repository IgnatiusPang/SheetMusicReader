# Cantabile (Dancla / Applebaum) – Clean Engraving Plan & Handover

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-10-22 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

## Goal
Reproduce `data/cantabile.jpeg` (photographed, pencil-annotated AMEB List A No 1 score) as a clean
engraved PDF with no pencil markings. `data/cantabile_engraved.pdf` was the work-in-progress; its red
Stamp annotations mark measures the user found wrong, unmarked measures were to be kept.

## Deliverables
| File | Purpose |
| --- | --- |
| `digitized_scores/cantabile.ly` | LilyPond 2.26 source, transcribed from the photo (single source of truth) |
| `data/cantabile_final.pdf` | Clean engraved A4 page, 9 systems, 41 measures, no annotations |
| `digitized_scores/cantabile.midi` | MIDI from the same source (♩ = 88) for aural comparison with the recording (see `references.md` item 7) |
| `omr_pointcloud.py` | Notehead point-cloud OMR: photo vs engraved PDF per-system alignment |
| `tests/test_omr_pointcloud.py` | Unit tests for the verifier (18 assertions, all passing) |

## Method
1. Per-system deskew of the photo (projection-profile variance), then linear staff-line fits refined
   locally (±40 px) for every notehead so page curvature does not shift pitches.
2. Filled noteheads = morphological opening (vertical SE removes staff lines, disk SE removes stems,
   beams, slurs); hollow noteheads = small elliptical holes after bridging the staff line.
3. Engraved PDF noteheads read exactly with `pdfplumber` (Emmentaler glyph origins), systems from the
   staff-line objects, red `Stamp` annotations mapped to the nearest notehead.
4. The two pitch sequences are aligned per system with a monotone sequence matcher (`difflib`).
   A full optimal-transport alignment (ManifoldFGW) is unnecessary here because each system is a
   1-D ordered sequence; the monotone alignment is exact and cheap.
5. Final verification: all 9 systems align with no pitch substitution (remaining diffs are hollow
   heads the photo detector misses and text/fingering blobs, both tool artefacts).

Run: `python omr_pointcloud.py compare data/cantabile.jpeg data/cantabile_final.pdf`
(`stamps <pdf>` maps reviewer red marks to noteheads; `crops <photo> OUT_DIR` writes labelled proof crops.)
Step-by-step procedure: `notes/session_handover_20261022_2330.md`.

## Corrections to red-marked measures (WIP → final)
| m | WIP | Final (from photo) |
| --- | --- | --- |
| 3, 11, 27 | G5. A5 B5 D5 | F♯5. G5 A5 D5 |
| 5 | D5. B4 D5 C5 B4 A4 | D5. B4 D5 C5 A4 D5 |
| 6 | D5(half) B4 D5 C5 A4 | D5. B4 D5 C5 A4 D5 (no fingering/bow on the first note) |
| 7 | D5. B4(♪) C5 E5 | D5 B4 C5 E5, four quarters |
| 13 | A5(♩) F♯5 A5 G5 E5 A5 | A5. F♯5 A5 G5 E5 A5 |
| 14 | A5(half) F♯5 A5 G5 E5 | A5. F♯5 A5 G5 E5 A5 |
| 15 | 7 notes, `f` | A5 F♯5 D5 B4 A4 B4 G4 A4 (eight ♪); `f` belongs to m13 |
| 16 | A4 F♯4 A4 D5 B4 A4 B4 G4 | F♯4 A4 D5 B4 A4 B4 G4 A4 |
| 17 | A4 F♯4 A4 D5 | F♯4 A4 G4 B4 |
| 18 | F5 A5 F5 C5 | D5 F♯5 E5 C♯5 |
| 19, 21 | wrong rhythm | D5 half, then ♪ C♯5 D5 E5 D5 |
| 20, 22 | C♯5. B5 … | C♯5 B5 A5 C♯5, four quarters |
| 24 | C5 | (♮)C5 cautionary natural |
| 25 | D5 | (♮)D5 cautionary natural |
| 30 | fingerings 2, 1 and slur F5–E5 | removed (not in print; only `0` on E5) |
| 32 | G5 half-dotted, F♯5 G5 | G5 half, F♯5 G5 A5 G5 |
| 34 | C5 B4 C5 D5 | B4 C5 D5 C5 |

## Changes in unmarked measures (faithful to the print – veto if unwanted)
- Slurs the WIP drew between pairs of half notes (m4, 8, 26, 28, 33, 35) are not in the print; dropped.
- Hairpins not in the print dropped (m4, 28, 33); printed decrescendo m23 beat 3 → m24 added; `p` at m25 added.
- Second down-bow in m23 dropped; `dim.` printed without trailing dashes; time signature shown as 4/4.

## Next steps
- Listen to `digitized_scores/cantabile.midi` against the recording for a final aural check.
- Optional: convert `cantabile.ly` to MusicXML (`python-ly` or MuseScore import) for the app library.
- Optional: retire the superseded `data/cantabile_cleaned.pdf` and `data/cantabile_engraved.pdf`
  (Rule 1, deduplicated library) once the final has been accepted.

<!-- APAF Bioinformatics | R_is_for_Robot | Approved -->
