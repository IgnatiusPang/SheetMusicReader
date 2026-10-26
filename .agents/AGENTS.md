# Sheet Music Reader - Workspace Rules

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-07-28 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

## Sheet Music Reading & Engraving Rules

### Rule 1: Deduplicated Score Library Hygiene
- The workspace maintains a clean, deduplicated library of unique Psalm scores in `data/` and `digitized_scores/`.
- No duplicate titles or redundant PDF score files are allowed.

### Rule 2: Standard Treble Staff Engraving Layout Order
- Every system row of music on a 5-line staff MUST render components in strict left-to-right order:
  1. **5 Horizontal Staff Lines**: `E4` (line 1), `G4` (line 2), `B4` (line 3), `D5` (line 4), `F5` (line 5) with uniform 12px line spacing.
  2. **Treble Clef (`𝄞` / `U+1D11E`)**: Anchored at `x = 10px`, with G-clef loop centered on line 2 (`G4`, `y = 76px`).
  3. **Key Signature Accidentals**: Placed immediately to the right at `x = 50px` on exact staff lines/spaces:
     - **Sharps (`♯`)**: `F5` (line 5), `C5` (space 3), `G5` (space above staff), `D5` (line 4), `A4` (space 2), `E5` (space 4), `B4` (line 3).
     - **Flats (`♭`)**: `B4` (line 3), `E5` (space 4), `A4` (space 2), `D5` (line 4), `G4` (line 2), `C5` (space 3), `F4` (space 1).
  4. **Time Signature**: Placed immediately after key signature (`x = 50 + key_width + 8px`), stacked top numerator over bottom denominator spanning staff lines 1 to 5.
  5. **Start Measure Bar Line**: Vertical line connecting lines 1–5 at `x = time_x + 28px`.
  6. **Note & Rest Layer**: First measure notes start right after the start bar line with dynamic offset padding.

### Rule 3: Optical Music Recognition (OMR) Rules
- **Rule 3.1: 5-Line Staff Row Detection**: 5 parallel lines with width > 100px define staff system rows.
- **Rule 3.2: Coordinate Pitch Mapping**: Vertical notehead center Y position calculates diatonic pitch relative to line 1 (`E4`) and line 5 (`F5`).
- **Rule 3.3: Duration & Stem Fill**: Hollow notehead = minim/half note; filled notehead = crotchet/quarter note; no stem = semibreve/whole note. Stems UP on right side for notes below `B4`, stems DOWN on left side for notes on/above `B4`.
- **Rule 3.4: Multi-Note Polyphonic Chords**: Noteheads stacked at the same X position ($|x_1 - x_2| < 8\text{px}$) form polyphonic chords.
- **Rule 3.5: Tie Arc Symbol (`◡`)**: Curved bezier arcs bridging adjacent noteheads of identical pitch assign `tie: "start"` and `tie: "stop"`, sustaining sound without re-striking notes.
- **Rule 3.6: Key Signature Accidentals in Synthesis**: Key signature accidentals (`4#` = `F#`, `C#`, `G#`, `D#`) automatically modify diatonic notes to sound their exact sharp MIDI pitches in audio playback and light up black keys on the 61-key piano keyboard visualizer.
- **Rule 3.7: Silent Rest Symbols**: Quarter (`𝄽`), half (`𝄼`), whole (`𝄻`), and eighth (`𝄾`) rests render centered on the staff and pause synth audio for their duration.
- **Rule 3.8: Stem Beaming for Consecutive Short Notes**: Two or more consecutive eighth (`0.5b`) or sixteenth (`0.25b`) notes within a measure are joined at stem tops by thick horizontal beam bar lines (`━`).

### Rule 4: Automated Test Suite Requirement
- Every layout placement rule, OMR feature, key signature, time signature, and rest symbol MUST have corresponding automated unit test assertions in `tests/test_pdf_extraction.py`, `tests/test_flask_routes.py`, and `tests/test_app.py`. All tests must pass cleanly (`pytest`).

<!-- APAF Bioinformatics | R_is_for_Robot | Approved -->
