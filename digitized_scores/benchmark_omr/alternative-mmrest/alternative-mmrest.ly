\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Alternative Mmrest"
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
  \numericTimeSignature \clef treble \key c \major \time 3/4 \partial 4
  % system 1
  c'4 |  % bar 1
  \set Timing.measureLength = #1 c'1 | \set Timing.measureLength = #3/4  % bar 2
  c'2. |  % bar 3
  r2. |  % bar 4
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
  \numericTimeSignature \clef treble \key c \major \time 3/4 \partial 4
  % system 1
  c'4 |  % bar 1
  \set Timing.measureLength = #1 c'1 | \set Timing.measureLength = #3/4  % bar 2
  c'2. |  % bar 3
  r2. |  % bar 4
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
