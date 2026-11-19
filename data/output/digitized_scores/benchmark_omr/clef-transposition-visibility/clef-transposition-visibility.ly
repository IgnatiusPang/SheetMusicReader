\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Clef Transposition Visibility"
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
  c''2 c''2 |  % bar 1
  c''2 c''2 |  % bar 2
  \break
  % system 2
  \key c \major c''2 \clef tenor c'2 |  % bar 3
  b2 b2 |  % bar 4
  b2 b2 |  % bar 5
  \break
  % system 3
  \clef treble c''2 c''2 |  % bar 6
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
  c''2 c''2 |  % bar 1
  c''2 c''2 |  % bar 2
  \break
  % system 2
  \key c \major c''2 \clef tenor c'2 |  % bar 3
  b2 b2 |  % bar 4
  b2 b2 |  % bar 5
  \break
  % system 3
  \clef treble c''2 c''2 |  % bar 6
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
