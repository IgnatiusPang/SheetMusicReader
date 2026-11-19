\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Auto Beam Bar"
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
  \set Timing.measureLength = #3/8 c'8[ c'8 c'8] | \set Timing.measureLength = #1/4  % bar 1
  \set Timing.measureLength = #3/4 c'8[ c'8 c'8 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #1/4  % bar 2
  \set Timing.measureLength = #3/8 c'8[ c'8 c'8] | \set Timing.measureLength = #1/4  % bar 3
  \set Timing.measureLength = #3/8 c'16[ c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #1/4  % bar 4
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
  \set Timing.measureLength = #3/8 c'8[ c'8 c'8] | \set Timing.measureLength = #1/4  % bar 1
  \set Timing.measureLength = #3/4 c'8[ c'8 c'8 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #1/4  % bar 2
  \set Timing.measureLength = #3/8 c'8[ c'8 c'8] | \set Timing.measureLength = #1/4  % bar 3
  \set Timing.measureLength = #3/8 c'16[ c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #1/4  % bar 4
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
