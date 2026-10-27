\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Beam Rest"
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
  \set Timing.measureLength = #9/8 e,8 r16 f,16[ d8 e16 e16] c4 c16 r16 bes,8 r16 c16 | \set Timing.measureLength = #1  % bar 1
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
  \set Timing.measureLength = #9/8 e,8 r16 f,16[ d8 e16 e16] c4 c16 r16 bes,8 r16 c16 | \set Timing.measureLength = #1  % bar 1
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
