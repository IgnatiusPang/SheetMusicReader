\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Beam Subdivide Tuplet Boundaries"
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
  \numericTimeSignature \clef treble \key c \major \time 2/4
  % system 1
  \set Timing.measureLength = #33/64 c'16[ c'32 c'32 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1/2  % bar 1
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
  \numericTimeSignature \clef treble \key c \major \time 2/4
  % system 1
  \set Timing.measureLength = #33/64 c'16[ c'32 c'32 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #1/2  % bar 1
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
