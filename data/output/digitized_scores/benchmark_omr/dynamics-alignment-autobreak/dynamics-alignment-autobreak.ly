\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Dynamics Alignment Autobreak"
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
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  c'1 |  % bar 1
  c'1 |  % bar 2
  a1 |  % bar 3
  c'1 |  % bar 4
  c'1 |  % bar 5
  c'1 |  % bar 6
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
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  c'1 |  % bar 1
  c'1 |  % bar 2
  a1 |  % bar 3
  c'1 |  % bar 4
  c'1 |  % bar 5
  c'1 |  % bar 6
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
