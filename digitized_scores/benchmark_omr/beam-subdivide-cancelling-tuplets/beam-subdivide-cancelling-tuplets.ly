\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Beam Subdivide Cancelling Tuplets"
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
  \numericTimeSignature \clef treble \key c \major \time 1/4
  % system 1
  \set Timing.measureLength = #3/8 c'16[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'16] | \set Timing.measureLength = #1/4  % bar 1
  \break
  % system 2
  \key c \major \set Timing.measureLength = #3/8 c'16[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'16] | \set Timing.measureLength = #1/4  % bar 2
  \break
  % system 3
  \clef alto \set Timing.measureLength = #3/8 d16[ d32 d32 d32 d32 d32 d32 d32 d32 d16] | \set Timing.measureLength = #1/4  % bar 3
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
  \numericTimeSignature \clef treble \key c \major \time 1/4
  % system 1
  \set Timing.measureLength = #3/8 c'16[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'16] | \set Timing.measureLength = #1/4  % bar 1
  \break
  % system 2
  \key c \major \set Timing.measureLength = #3/8 c'16[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'16] | \set Timing.measureLength = #1/4  % bar 2
  \break
  % system 3
  \clef alto \set Timing.measureLength = #3/8 d16[ d32 d32 d32 d32 d32 d32 d32 d32 d16] | \set Timing.measureLength = #1/4  % bar 3
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
