\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Auto Beam Exceptions"
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
  \numericTimeSignature \clef treble \key c \major \time 3/4 \partial 2
  % system 1
  c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] |  % bar 1
  c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] |  % bar 2
  r2. |  % bar 3
  \break
  % system 2
  \key c \major c'8[ c'32 c'32 c'32 c'32 c'16 c'16 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] r32 |  % bar 4
  \break
  % system 3
  \set Timing.measureLength = #35/32 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #3/4  % bar 5
  \break
  % system 4
  \time 6/8 \set Timing.measureLength = #13/16 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #3/4  % bar 6
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
  \numericTimeSignature \clef treble \key c \major \time 3/4 \partial 2
  % system 1
  c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] |  % bar 1
  c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] |  % bar 2
  r2. |  % bar 3
  \break
  % system 2
  \key c \major c'8[ c'32 c'32 c'32 c'32 c'16 c'16 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] r32 |  % bar 4
  \break
  % system 3
  \set Timing.measureLength = #35/32 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #3/4  % bar 5
  \break
  % system 4
  \time 6/8 \set Timing.measureLength = #13/16 c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] | \set Timing.measureLength = #3/4  % bar 6
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
