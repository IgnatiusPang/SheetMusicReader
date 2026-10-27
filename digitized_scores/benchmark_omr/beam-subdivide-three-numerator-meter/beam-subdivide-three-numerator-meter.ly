\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Beam Subdivide Three Numerator Meter"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
  ragged-last = ##f
  system-system-spacing.basic-distance = #16
}
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 2/8
  % system 1
  \set Timing.measureLength = #13/32 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1/4  % bar 1
  \break
  % system 2
  \clef alto \time 4/16 \set Timing.measureLength = #3/8 d32[ d32 d32 d32 d32 d32 d32 d32 d32 d32 d32 d32] | \set Timing.measureLength = #1/4  % bar 2
  d8. d16 |  % bar 3
  d16[ d8] r16 |  % bar 4
  \break
  % system 3
  \clef mezzosoprano \time 1/2 f32[ d32 d32 d32 d32 d32 d32 d32 d32 d32 d32 d32] r8 |  % bar 5
  d16.[ d32] r4. |  % bar 6
  d32[ d16] r4. r32 |  % bar 7
  \bar "|."
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    
  }
}
}
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 2/8
  % system 1
  \set Timing.measureLength = #13/32 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1/4  % bar 1
  \break
  % system 2
  \clef alto \time 4/16 \set Timing.measureLength = #3/8 d32[ d32 d32 d32 d32 d32 d32 d32 d32 d32 d32 d32] | \set Timing.measureLength = #1/4  % bar 2
  d8. d16 |  % bar 3
  d16[ d8] r16 |  % bar 4
  \break
  % system 3
  \clef mezzosoprano \time 1/2 f32[ d32 d32 d32 d32 d32 d32 d32 d32 d32 d32 d32] r8 |  % bar 5
  d16.[ d32] r4. |  % bar 6
  d32[ d16] r4. r32 |  % bar 7
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
