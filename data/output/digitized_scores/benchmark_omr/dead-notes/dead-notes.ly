\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Dead Notes"
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
  e,8. e,16 g,4 a,4 b,4 |  % bar 1
  e8. e16 g4 a4 b4 |  % bar 2
  e4. e8[ e8 e8] e4 |  % bar 3
  <e e,>8[ <e e,>8] <e e,>4 <e e,>4 r4 |  % bar 4
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
  e,8. e,16 g,4 a,4 b,4 |  % bar 1
  e8. e16 g4 a4 b4 |  % bar 2
  e4. e8[ e8 e8] e4 |  % bar 3
  <e e,>8[ <e e,>8] <e e,>4 <e e,>4 r4 |  % bar 4
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
