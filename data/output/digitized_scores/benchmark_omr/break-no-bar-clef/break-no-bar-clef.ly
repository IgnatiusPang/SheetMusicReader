\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Break No Bar Clef"
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
  c'2 |  % bar 1
  \break
  % system 2
  \key c \major c'2 |  % bar 2
  \break
  % system 3
  \clef bass c'2 |  % bar 3
  \break
  % system 4
  c'2 |  % bar 4
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
  c'2 |  % bar 1
  \break
  % system 2
  \key c \major c'2 |  % bar 2
  \break
  % system 3
  \clef bass c'2 |  % bar 3
  \break
  % system 4
  c'2 |  % bar 4
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
