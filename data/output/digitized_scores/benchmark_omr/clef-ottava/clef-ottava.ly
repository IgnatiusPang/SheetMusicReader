\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Clef Ottava"
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
  \numericTimeSignature \clef alto \key c \major \time 4/4
  % system 1
  a'4 b'4 c''4 a'4 |  % bar 1
  a4 b4 c'4 a4 |  % bar 2
  \clef bass a4 b4 c'4 a4 |  % bar 3
  a,4 b,4 c4 a,4 |  % bar 4
  \clef treble a''4 b''4 c'''4 a''4 |  % bar 5
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
  \numericTimeSignature \clef alto \key c \major \time 4/4
  % system 1
  a'4 b'4 c''4 a'4 |  % bar 1
  a4 b4 c'4 a4 |  % bar 2
  \clef bass a4 b4 c'4 a4 |  % bar 3
  a,4 b,4 c4 a,4 |  % bar 4
  \clef treble a''4 b''4 c'''4 a''4 |  % bar 5
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
