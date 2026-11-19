\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\paper { indent = 0 tagline = ##f line-width = 190\mm ragged-right = ##f }
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4 \set Score.currentBarNumber = #11
  % system 3
  fis''4.\ff( g''8) a''4( d''4) |  % bar 11
  b''2 g''2 |  % bar 12
  a''4.\downbow\f( fis''8) a''8( g''8 e''8 a''8) |  % bar 13
  a''4.( fis''8) a''8( g''8 e''8 a''8) |  % bar 14
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \override BarNumber.break-visibility = ##(#f #t #t)
    barNumberVisibility = #all-bar-numbers-visible
  }
}
}
