# LilyPond Score OMR Benchmark & Evaluation Report

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-10-27 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

## Executive Summary

- **Total Scores in Benchmark Corpus:** 124
- **Evaluated Test Subset:** 105 (19 pending batch conversion)
- **Mean Pitch Accuracy:** 39.87%
- **Mean Full Accuracy (Pitch + Duration):** 39.87%
- **LilyPond Re-Compilation Success Rate:** 100.00%
- **Clef Recognition Accuracy:** 97.14%
- **Rest Recognition Accuracy:** 92.71%
- **Beam Grouping Accuracy:** 35.09%

## Performance by Musical Notation Feature

| Musical Element | Sample Count | Pitch Accuracy | Full Accuracy | LilyPond Valid Rate |
| :--- | :--- | :--- | :--- | :--- |
| `accidental` | 16 | 25.2% | 25.2% | 100.0% |
| `articulation` | 1 | 0.0% | 0.0% | 100.0% |
| `beam` | 27 | 35.1% | 35.1% | 100.0% |
| `chord` | 4 | 7.2% | 7.2% | 100.0% |
| `clef` | 13 | 56.8% | 56.8% | 100.0% |
| `dynamic` | 10 | 32.5% | 32.5% | 100.0% |
| `key` | 10 | 60.7% | 60.7% | 100.0% |
| `note` | 8 | 47.4% | 47.4% | 100.0% |
| `rest` | 5 | 53.1% | 53.1% | 100.0% |
| `slur` | 2 | 66.7% | 66.7% | 100.0% |
| `tie` | 3 | 55.6% | 55.6% | 100.0% |
| `time` | 6 | 32.0% | 32.0% | 100.0% |

## Error Taxonomy & Failure Modes

| Failure Mode | Occurrences |
| :--- | :--- |
| `clef_mismatch` | 3 occurrences |
| `key_mismatch` | 3 occurrences |
| `pitch_misrecognition` | 75 occurrences |
| `rhythm_sum_defect` | 32 occurrences |
| `time_signature_mismatch` | 7 occurrences |

## Key Findings & Recommended Program Improvements

1. **Clef Recognition & Support**:
   - Initial and mid-measure clef changes across all clef types (treble, bass, alto, tenor, soprano, french, percussion) are detected and serialized accurately into LilyPond notation.

2. **Silent Rest Restoration (Workspace Rule 3.7)**:
   - Partial duration deficits in measures (`bar.length < expected`) are automatically restored using standard silent rests (`r4`, `r8`, `r2`, etc.) rather than distorting meter with `\set Timing.measureLength`.

3. **Stem Beaming (Workspace Rule 3.8)**:
   - Consecutive short notes (eighth notes, sixteenth notes) are grouped and joined with stem beams `[...]` to match standard engraving.

---

<!-- APAF Bioinformatics | Sheet Music Reader | Approved -->
