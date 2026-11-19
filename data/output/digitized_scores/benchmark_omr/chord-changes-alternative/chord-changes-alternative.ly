\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Chord Changes Alternative"
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
  g'4\fermata f'4 e'4 d'4 |  % bar 1
  c'4 r4 r4 r4 |  % bar 2
  c'4 g4 c'4\fermata r4 |  % bar 3
  b4 g4 c'2\fermata |  % bar 4
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
  g'4\fermata f'4 e'4 d'4 |  % bar 1
  c'4 r4 r4 r4 |  % bar 2
  c'4 g4 c'4\fermata r4 |  % bar 3
  b4 g4 c'2\fermata |  % bar 4
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
