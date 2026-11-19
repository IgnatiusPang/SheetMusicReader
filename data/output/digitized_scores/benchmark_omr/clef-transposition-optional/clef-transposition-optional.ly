\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Clef Transposition Optional"
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
  \numericTimeSignature \clef bass \key c \major \time 4/4
  % system 1
  b,1 |  % bar 1
  \set Timing.measureLength = #2 c1 \clef tenor a1 | \set Timing.measureLength = #1  % bar 2
  a1 |  % bar 3
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
  \numericTimeSignature \clef bass \key c \major \time 4/4
  % system 1
  b,1 |  % bar 1
  \set Timing.measureLength = #2 c1 \clef tenor a1 | \set Timing.measureLength = #1  % bar 2
  a1 |  % bar 3
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
