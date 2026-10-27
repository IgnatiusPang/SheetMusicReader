\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Duration Line Tie"
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
  a'1( |  % bar 1
  g'1) |  % bar 2
  g'1 |  % bar 3
  f'1 |  % bar 4
  \break
  % system 2
  \key c \major a'1( |  % bar 5
  a'1) |  % bar 6
  g'1 |  % bar 7
  f'1 |  % bar 8
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
  a'1( |  % bar 1
  g'1) |  % bar 2
  g'1 |  % bar 3
  f'1 |  % bar 4
  \break
  % system 2
  \key c \major a'1( |  % bar 5
  a'1) |  % bar 6
  g'1 |  % bar 7
  f'1 |  % bar 8
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
