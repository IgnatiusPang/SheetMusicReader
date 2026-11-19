---
name: lean4-music-verification
description: >-
  Formally verify sheet music translations across PDF, MusicXML, GNU LilyPond,
  MIDI, and slowed practice editions using the Lean 4 theorem prover (`formalization/lean/`).
  Checks exact integer-tick bar-beat conservation (48 ticks per quarter, 192 per whole)
  and Gate D5 cross-format sounding-note equivalence. Use whenever validating that a
  converted or slowed score stays mathematically true to the original.
---

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-11-15 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

# Lean 4 Sheet Music Verification

Use this skill when you want mathematical certainty that converting sheet music between **PDF**, **MuseScore MusicXML (`.musicxml`)**, **GNU LilyPond (`.ly`)**, **MIDI (`.mid`)**, and **slowed/augmented practice editions** never drops a note, changes a pitch, breaks a tie, or miscounts beats in any bar (see `references.md` items 24, 26, and 27).

---

## How the Formal Verification Works

1. **Exact Integer Tick Grid (`48` ticks per quarter, `192` per whole)**:
   Standard binary, dotted, double-dotted, triplet (`16` or `32` ticks), and duplet subdivisions are represented as exact natural numbers (`Nat`) without floating-point rounding drift.
2. **Universal Machine-Checked Theorems (`formalization/lean/SheetMusic/`)**:
   - **Bar-Beat Conservation**: Every bar satisfies `beatType * expectedTicks = beats * 192` and `barTicks events = expectedTicks`.
   - **Rest Completion (`appendRest_valid`)**: Appending a silent rest equal to a bar's deficit restores exact bar validity without changing sounding notes.
   - **Tie Merging (`mergeTies_conserves_ticks`)**: Merging adjacent tied notes of matching pitches strictly preserves total sounding duration.
   - **Slowdown & Rhythmic Augmentation (`scaleTempo_duration_law`, `augmentScore_preserves_laws`)**: Scaling playback tempo (`speedNum / speedDen`) leaves every note and bar valid while scaling elapsed playback duration cleanly; multiplying all written note values by integer `k > 0` (`augmentScore`) preserves bar validity and multiplies sounding ticks by `k`.
   - **Cross-Format Equivalence (`checkScoreEquiv_iff`, `scoreEquiv_trans`)**: Equivalence holds across multi-step translations when all bars are valid and flattened sounding-note streams match.
3. **Anti-Self-Comparison Guarantee (`lean_bridge.py`)**:
   Instead of trusting in-memory structures, `lean_bridge.py` independently re-parses the **written files on disk** (`.musicxml`, `.ly`, `.mid`) and feeds them to the compiled Lean 4 `score_verifier` kernel binary (`formalization/lean/.lake/build/bin/score_verifier`), plus optional standalone `<stem>_cert.lean` files checked directly with `lake env lean`.

---

## CLI Verification Commands

```bash
# Convert a PDF or JSON score into MusicXML, LilyPond, MIDI, WAV, AND generate + check a standalone Lean 4 kernel certificate:
python3 -m sheet_music_reader.cli.music_pipeline convert data/input/psalms/03_Ps104103-Lord-Send-Out-Your-Spirit-Chart.pdf \
    --out-dir data/output/practice/verified_score \
    --speeds 1.0,0.5,0.25 \
    --lean-cert

# Verify existing MusicXML, LilyPond, and MIDI files on disk against a source score:
python3 -m sheet_music_reader.cli.music_pipeline verify path/to/source.pdf \
    --musicxml data/output/practice/score.musicxml \
    --lilypond data/output/practice/score.ly \
    --midi data/output/practice/score.mid \
    --speed 0.5 \
    --lean-cert data/output/practice/score_cert.lean
```

Inside the web app, click **✓ Lean 4 Verify** to run real-time disk-based verification on the currently selected score and speed (`GET /api/psalms/<id>/verify?speed=<ratio>`).

---

## Building or Re-Auditing the Lean 4 Formalization

```bash
cd formalization/lean
lake build
./.lake/build/bin/test_runner
```

All proofs depend exclusively on Lean core axioms (`propext`, `Classical.choice`, `Quot.sound`) with zero `sorry`, zero custom axioms, and zero `native_decide`.

---

## Interpreting Failures & Fixes

- **`bar N: got X ticks, expected Y ticks`**: A measure does not add up to the time signature. Check for a missing rest, dropped dot, or split tie in bar `N`. If the score intentionally begins or ends with an incomplete pickup bar, pass `--pad-rests` to complete bars with explicit silent rests via `appendRest_valid`.
- **`note index I mismatch`**: A note pitch or tied duration differs between formats on disk (`<stem>.musicxml`, `<stem>.ly`, or `<stem>.mid`). Inspect measure context around sounding note `I` and regenerate cleanly.

<!-- APAF Bioinformatics | SKILL.md | Approved | 2026-11-15 -->
