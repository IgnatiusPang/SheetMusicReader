\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Accidental Ancient"
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
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  cis''4 cis''4 ces''4 |  % bar 1
  c''4 c''4 ces''4 |  % bar 2
  c''4 c''4 ces''4 |  % bar 3
  c''4 c''4 ces''4 |  % bar 4
  c''4 c''4 ces''4 |  % bar 5
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
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  cis''4 cis''4 ces''4 |  % bar 1
  c''4 c''4 ces''4 |  % bar 2
  c''4 c''4 ces''4 |  % bar 3
  c''4 c''4 ces''4 |  % bar 4
  c''4 c''4 ces''4 |  % bar 5
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
