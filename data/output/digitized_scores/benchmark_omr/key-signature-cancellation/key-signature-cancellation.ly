\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Key Signature Cancellation"
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
  \numericTimeSignature \clef treble \key a \major \time 4/4
  % system 1
  g'1 |  % bar 1
  \key ges \major g'1 |  % bar 2
  \key c \major g'1 |  % bar 3
  g'1 |  % bar 4
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
  \numericTimeSignature \clef treble \key a \major \time 4/4
  % system 1
  g'1 |  % bar 1
  \key ges \major g'1 |  % bar 2
  \key c \major g'1 |  % bar 3
  g'1 |  % bar 4
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
