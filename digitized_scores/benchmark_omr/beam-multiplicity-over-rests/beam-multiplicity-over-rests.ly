\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Beam Multiplicity Over Rests"
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
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  \set Timing.measureLength = #35/32 c'8 r16 c'32[ c'32 c'32] r16 c'32[ c'8 c'32 c'32] r16. c'32[ c'32( c'16.) c'32 c'32 c'32] r16 c'8 | \set Timing.measureLength = #3/4  % bar 1
  c'16 r32 c'32 r16 c'16[ c'16] r16 c'32 r32 c'16 r4 |  % bar 2
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
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  \set Timing.measureLength = #35/32 c'8 r16 c'32[ c'32 c'32] r16 c'32[ c'8 c'32 c'32] r16. c'32[ c'32( c'16.) c'32 c'32 c'32] r16 c'8 | \set Timing.measureLength = #3/4  % bar 1
  c'16 r32 c'32 r16 c'16[ c'16] r16 c'32 r32 c'16 r4 |  % bar 2
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
