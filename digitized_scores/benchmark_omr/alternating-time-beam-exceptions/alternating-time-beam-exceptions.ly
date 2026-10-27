\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Alternating Time Beam Exceptions"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
  ragged-last = ##f
  system-system-spacing.basic-distance = #16
}
\score {
\new PianoStaff <<
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key f \major \time 2/2
  % system 1
  c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] |  % bar 1
  \time 4/4 \set Timing.measureLength = #9/8 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #1  % bar 2
  \break
  % system 2
  \key c \major \time 8/8 c'8[ c'8 c'8] r2 r8 |  % bar 3
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] r16 |  % bar 4
  \break
  % system 3
  \time 4/4 \set Timing.measureLength = #17/16 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #1  % bar 5
  \time 8/8 c'16[ c'16 c'16 c'16 c'16 c'16 c'16] r2 r16 |  % bar 6
  \break
  % system 4
  \time 2/2 \set Timing.measureLength = #9/8 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1  % bar 7
  \break
  % system 5
  \time 4/4 \set Timing.measureLength = #17/16 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1  % bar 8
  \time 8/8 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] r2 r32 |  % bar 9
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key f \major \time 2/2
  % system 1
  c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] |  % bar 1
  \time 4/4 \set Timing.measureLength = #9/8 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #1  % bar 2
  \break
  % system 2
  \key c \major \time 8/8 c'8[ c'8 c'8] r2 r8 |  % bar 3
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] r16 |  % bar 4
  \break
  % system 3
  \time 4/4 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] |  % bar 5
  \time 8/8 c'16[ c'16 c'16 c'16 c'16 c'16 c'16] r2 r16 |  % bar 6
  \break
  % system 4
  \time 2/2 \set Timing.measureLength = #33/32 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1  % bar 7
  \break
  % system 5
  \time 4/4 \set Timing.measureLength = #17/16 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 <c' c'>32 <c' c'>32] | \set Timing.measureLength = #1  % bar 8
  \time 8/8 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] r2 r32 |  % bar 9
  \bar "|."
}
>>
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    
  }
}
}
\score {
\new PianoStaff <<
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key f \major \time 2/2
  % system 1
  c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] |  % bar 1
  \time 4/4 \set Timing.measureLength = #9/8 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #1  % bar 2
  \break
  % system 2
  \key c \major \time 8/8 c'8[ c'8 c'8] r2 r8 |  % bar 3
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] r16 |  % bar 4
  \break
  % system 3
  \time 4/4 \set Timing.measureLength = #17/16 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #1  % bar 5
  \time 8/8 c'16[ c'16 c'16 c'16 c'16 c'16 c'16] r2 r16 |  % bar 6
  \break
  % system 4
  \time 2/2 \set Timing.measureLength = #9/8 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1  % bar 7
  \break
  % system 5
  \time 4/4 \set Timing.measureLength = #17/16 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1  % bar 8
  \time 8/8 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] r2 r32 |  % bar 9
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key f \major \time 2/2
  % system 1
  c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] |  % bar 1
  \time 4/4 \set Timing.measureLength = #9/8 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #1  % bar 2
  \break
  % system 2
  \key c \major \time 8/8 c'8[ c'8 c'8] r2 r8 |  % bar 3
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] r16 |  % bar 4
  \break
  % system 3
  \time 4/4 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] |  % bar 5
  \time 8/8 c'16[ c'16 c'16 c'16 c'16 c'16 c'16] r2 r16 |  % bar 6
  \break
  % system 4
  \time 2/2 \set Timing.measureLength = #33/32 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1  % bar 7
  \break
  % system 5
  \time 4/4 \set Timing.measureLength = #17/16 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 <c' c'>32 <c' c'>32] | \set Timing.measureLength = #1  % bar 8
  \time 8/8 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] r2 r32 |  % bar 9
  \bar "|."
}
>>
\midi { \tempo 4 = 90 }
}
