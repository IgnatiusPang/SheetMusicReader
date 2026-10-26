---
author: Ignatius Pang
ai_assist: Claude Code (Claude Opus 5.5; earlier part of the session Claude Fable 5.1)
created: 2026-10-25
modified: 2026-10-25
purpose: Session handover — SheetMusicReader / psalm PDFs to MIDI
filename_convention: notes/session_handover_YYYYMMDD_HHMM.md (MANDATORY SUFFIX)
---

# Handover: 2026-10-25 21:40 — Ignatius Pang

## Repository/Project
`~/Workings/2026/SheetMusicReader` (not a git repository)

## Session Summary
Built `vector_omr.py`, a reusable converter from notation-software PDFs to MIDI, and ran it on all 17 psalm
PDFs in `data/`. Pitches, accidentals, dots, flags, rests, clefs, key and time signatures are read from the
music-font characters. Stems, beams and ties are measured on a 288 dpi render. Every bar is checked against the
time signature, and a LilyPond proof is engraved for visual comparison with the original.

## Completed
- `vector_omr.py`: CLI `convert` (MIDI, `--proof` LilyPond PDF, `--report` JSON).
- `digitized_scores/vector_midi/*.mid` (17 files) and `report.json`; `digitized_scores/vector_proofs/*.pdf|.ly`.
  The older parser's `digitized_scores/*.mid` were left untouched.
- `tests/test_vector_omr.py`: 26 tests including an end-to-end Psalm 19 check; all 44 OMR tests pass.
- `.claude/skills/pdf-to-midi/SKILL.md`: the repeatable workflow and a symptom → fix table.
- README section "Convert Score PDFs to MIDI".

## Results (final run)
| | Count |
| --- | ---: |
| PDFs converted | 17 |
| Bars read | 730 |
| Bars adding up exactly | 662 |
| Short bars at line start/end (pickups, closings) | 67 |
| Suspect bars | 1 |
| Over-full bars | 0 |

The single suspect bar (Lord on the Day I Called, system 1 bar 4) is the refrain's closing bar followed by a verse
pickup on the same line, so it is correct notation. Proofs of Ps 19, 104, 106, 117 and 146 were compared with the
originals by eye.

## How it works (follow this next time)
1. `pdffonts` must list a music font: Leland/Bravura (SMuFL codes), MScore (MuseScore 2), Opus (Sibelius) or
   `TTE…` (Finale/Maestro via PostScript). Sibelius files come in two encodings, symbol-PUA (`U+F0xx`) and
   MacRoman-mapped Unicode (e.g. `œ` = byte 0xCF notehead); `_byte()` normalises both to the Sonata byte table.
2. Staves = 5 equally spaced horizontal line objects; systems = staves joined by a left-edge vertical.
3. Glyphs are assigned to the nearest staff. Cue-size glyphs are dropped by a size filter around the dominant notehead size.
4. Pitch = half-space steps above the bottom line from the glyph baseline (`page.height − matrix[5]`) plus the
   clef offset; key signature = accidentals between clef and first note; accidentals persist to the bar line.
5. Note length = head type, halved per beam or flag. Beams are counted on the render in a column 0.55 staff space
   beside the stem tip. Dots are a horizontal chain right of the head, with repeat-sign dot pairs excluded.
6. Tuplets: isolated digits 2–6 in a text font centred over n notes (2 → ×1.5, 3 → ×2/3). An over-full bar
   falls back to keeping the up-stem voice, then to a triplet search.
7. Ties: thin arcs on the render between consecutive same-pitch notes, with staff and ledger rows masked; ties across line breaks need arcs at both ends.
8. Tempo: digits right after "=" times the beat-unit glyph (half, quarter, eighth, dotted).
9. MIDI: track per staff position in the system (track 1 = melody), lanes padded per system, ties merged.

Bugs found and fixed while building, useful for future fonts: stems one pixel wide were skipped by coarse
sampling, Sibelius noteheads have about 1.8 pt of side bearing, short beamed stems failed a 2.6-space test, a
"(3/4)" alternative metre was misparsed, chord digits leaked into the tempo, metre must be score-wide, and
repeat dots were counted as augmentation dots.

## Addendum: response/verse structure (same day)
User request: check Psalm 80's verse pickup, and repeat the response after each verse, detected automatically.
- Psalm 80's pickup (D4 F4) was missing because Sibelius drew it with a special notehead (`OpusSpecial` byte 0x65)
  outside the bar count. Now read as `xhead`, kept out of the bar check, and treated as the verse pickup.
- New in `vector_omr.py`: `page_labels`, `assign_label`, `sections_of`, `tail_pickup`, `arrangement`,
  `playback_parts`. MIDI default order is R, V1, R, V2, …, R (or Final). `--as-written` restores the old order.
- All 17 PDFs get a structure; pickups found in Ps 80 (2 extra notes), Ps 19, 122, 33 (1 each), Ps 1 (4 in-bar,
  actually the lead-back of its repeated response).
- Tests: 47 pass (Psalm 80 pickup timing, Psalm 106 stacked verses, arrangement order).

## Unresolved
- Repeats and first/second endings inside a section play once as written (Ps 1's response repeat is not doubled).
- Tenor "(8)" clef marks are not read (Ps 96 lower staff sounds an octave high in the accompaniment track).
- Chord symbols (accompaniment) are not converted, although the app's JSON format has an accompaniment field.
- New MIDI files are not wired into the app's ids (`psalm_19_words` etc.); the old parser's `.mid` remain in use.

## Decisions Made
- Vector glyph reading instead of image OMR: exact pitches; raster used only for strokes.
- Bar-sum validation as the automatic correctness signal; proofs for visual confirmation.
- New outputs in separate folders, so nothing from the earlier parser was overwritten.

## Next Steps
1. Listen to a few MIDI files (e.g. Ps 19, Taste and See) against the printed scores.
2. Decide whether to replace the app's `digitized_scores/<id>.mid` with the new files (needs a filename → id map).
3. Optional: parse chord symbols into an accompaniment track; expand repeats/voltas.

## Dependencies or Blockers
None. Anaconda Python 3.13 (`numpy`, `pdfplumber`, `Pillow`, `mido`), poppler `pdftoppm`, LilyPond 2.26 for proofs.

<!-- APAF Bioinformatics | R_is_for_Robot | Approved -->
