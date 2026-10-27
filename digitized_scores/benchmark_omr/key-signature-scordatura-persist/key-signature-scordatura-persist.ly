\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Key Signature Scordatura Persist"
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
  \numericTimeSignature \clef treble \key bes \major \time 4/4
  % system 1
  f'4 f'4 a'4 bes'4 |  % bar 1
  fis''4 a'4 a'4 bes'4 |  % bar 2
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
  \numericTimeSignature \clef treble \key bes \major \time 4/4
  % system 1
  f'4 f'4 a'4 bes'4 |  % bar 1
  fis''4 a'4 a'4 bes'4 |  % bar 2
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
