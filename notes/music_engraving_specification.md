# Sheet Music Engraving & Staff Notation Specification

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-07-28 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

## Executive Summary
This document establishes the official technical specification for sheet music engraving, Optical Music Recognition (OMR) pitch mapping, and visual score rendering in the **Sheet Music Reader** application. The standards detailed herein strictly adhere to Elaine Gould's *Behind Bars: The Definitive Guide to Music Notation* and W3C MusicXML specifications.

---

## Section 1: Staff System Geometry & Layout Order

Every line of music rendered on a standard 5-line staff MUST follow a strict left-to-right component layout order:

```text
[ 5 Horizontal Lines ] ➔ [ Treble Clef 𝄞 ] ➔ [ Key Signature Accidentals ] ➔ [ Time Signature ] ➔ [ Start Bar Line ] ➔ [ Beamed Notes & Lyrics ]
```

### 1.1 Staff Lines Geometry
- **Line Count**: 5 horizontal parallel staff lines.
- **Line Heights**:
  - Line 5 (`F5`): $y = 40\text{px}$
  - Line 4 (`D5`): $y = 52\text{px}$
  - Line 3 (`B4`): $y = 64\text{px}$
  - Line 2 (`G4`): $y = 76\text{px}$
  - Line 1 (`E4`): $y = 88\text{px}$
- **Line Spacing**: Uniform $12\text{px}$ between adjacent lines.
- **Total Staff Height**: $4 \times 12\text{px} = 48\text{px}$.

---

## Section 2: Key Signatures & Accidental Rules

### 2.1 Key Signature Placement & Coordinates
- **Placement**: Placed immediately to the right of the clef leader at $x = 65\text{px}$.
- **Sharp Key Signature Order ($\sharp$)**: `F5`, `C5`, `G5`, `D5`, `A4`, `E5`, `B4` (FCGDAEB).
  - `F#5`: $y = 30\text{px}$ (Line 5)
  - `C#5`: $y = 48\text{px}$ (Space 3)
  - `G#5`: $y = 24\text{px}$ (Space above staff)
  - `D#5`: $y = 42\text{px}$ (Line 4)
  - `A#4`: $y = 60\text{px}$ (Space 2)
  - `E#5`: $y = 36\text{px}$ (Space 4)
  - `B#4`: $y = 54\text{px}$ (Line 3)
- **Flat Key Signature Order ($\flat$)**: `B4`, `E5`, `A4`, `D5`, `G4`, `C5`, `F4` (BEADGCF).
  - `Bb4`: $y = 46\text{px}$ (Line 3)
  - `Eb5`: $y = 28\text{px}$ (Space 4)
  - `Ab4`: $y = 52\text{px}$ (Space 2)
  - `Db5`: $y = 34\text{px}$ (Line 4)
  - `Gb4`: $y = 58\text{px}$ (Line 2)
  - `Cb5`: $y = 40\text{px}$ (Space 3)
  - `Fb4`: $y = 64\text{px}$ (Space 1)

### 2.2 Pitch Alteration in Audio & Visualizer Synthesis
Key signature accidentals automatically modify diatonic notehead pitches to their exact sharp or flat MIDI numbers:
- `4#` (E Major): Modifies `F` $\rightarrow$ `F#` ($66$), `C` $\rightarrow$ `C#` ($73$), `G` $\rightarrow$ `G#` ($68$), `D` $\rightarrow$ `D#` ($63$).
- `3b` (Eb Major): Modifies `B` $\rightarrow$ `Bb` ($70$), `E` $\rightarrow$ `Eb` ($63$), `A` $\rightarrow$ `Ab` ($68$).

---

## Section 3: Time Signatures & Meter Rules

### 3.1 Placement & Stacked Format
- **Placement**: Placed immediately to the right of the key signature ($x = x_{\text{key}} + w_{\text{key}} + 8\text{px}$).
- **Stacked Format**: Top number (numerator / beats per measure) stacked vertically over bottom number (denominator / beat unit), spanning lines 1 to 5.

### 3.2 Standard Meter Types
1. **Simple Quadruple (`4/4`)**: 4 crotchet/quarter-note beats per measure.
2. **Compound Duple (`6/8`)**: 2 dotted-quarter beats (6 quaver/eighth notes) per measure.
3. **Simple Triple (`3/4`)**: 3 crotchet/quarter-note beats per measure.
4. **Cut Time (`2/2`)**: 2 minim/half-note beats per measure.

---

## Section 4: Tail Organization & Stem Beaming

How note tails and stems are organized across measures:

### 4.1 Single Unbeamed Short Note (Flag Tail)
- A standalone isolated eighth note (`0.5b`) has a single curved flag (`𝄾`) attached to the tip of its stem.
- A standalone sixteenth note (`0.25b`) has a double flag attached to the stem tip.

### 4.2 Stem Beaming for Consecutive Notes (Beam Bars $━$)
- Two or more consecutive short notes (eighth or sixteenth notes) within a beat division are joined at stem tops by thick horizontal or slanted **Beam Bars ($━$)** ($5\text{px}$ thickness).
- When beam bars join stems, individual flags are omitted.

### 4.3 Beat-Grouped Pair Divisions
Beaming MUST reflect meter beat divisions rather than chaining across beat boundaries:
- **Simple Meters (`4/4`, `3/4`)**: Eighth notes are beamed in **discrete pairs of 2 per beat**.
- **Compound Meters (`6/8`)**: Eighth notes are beamed in **discrete beat groups (Pair 1, Pair 2)** representing each dotted-quarter beat division:

```text
Measure in 6/8: [ Note 1 + Note 2 ] ━━ [ Note 3 + Note 4 ] ━━ [ Note 5 (Dotted Half) ]
                 ^-- Pair 1 --^       ^-- Pair 2 --^
```

---

## Section 5: Tie Arc Symbols ($\text{◡}$) & Rest Symbols

### 5.1 Tie Arc Symbol ($\text{◡}$)
- **Definition**: Curved Bezier arc bridging adjacent noteheads of identical pitch.
- **Placement**: Drawn below notehead for stem-up notes, above notehead for stem-down notes.
- **Playback Engine**: Sustains tone continuously for combined duration without re-striking.

### 5.2 Silent Rest Symbols
- **Quarter Rest ($\mathbf{\unicode{x1D13D}}$)**: Centered on staff line 3 (`B4`).
- **Half Rest ($\mathbf{\unicode{x1D13C}}$)**: Sits on staff line 3 (`B4`).
- **Whole Rest ($\mathbf{\unicode{x1D13B}}$)**: Hangs below staff line 4 (`D5`).
- **Eighth Rest ($\mathbf{\unicode{x1D13E}}$)**: Centered on staff line 3 (`B4`).

---

## Section 6: Lyric Overlays & Chord Annotations

- **Chord Annotations**: Rendered above staff lines ($y = -20\text{px}$) in bold gold typography (`#FFD700`).
- **Lyric Syllables**: Positioned directly underneath corresponding noteheads ($y = +120\text{px}$), hyphenated between syllables (`go-`, `ing`).

---

<!-- APAF Bioinformatics | Sheet Music Reader | Approved -->
