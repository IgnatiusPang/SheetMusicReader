\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Completion Heads Tie"
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
  r2 d''2( |  % bar 1
  d''2)( d''2)( |  % bar 2
  d''2) d''2 |  % bar 3
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
  r2 d''2( |  % bar 1
  d''2)( d''2)( |  % bar 2
  d''2) d''2 |  % bar 3
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
