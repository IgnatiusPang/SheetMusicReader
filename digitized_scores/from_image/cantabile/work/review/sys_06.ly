\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\paper { indent = 0 tagline = ##f line-width = 190\mm ragged-right = ##f }
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4 \set Score.currentBarNumber = #28
  % system 7
  b''2 g''2 |  % bar 28
  b''4.( fis''8) a''8( g''8) d''8( b'8) |  % bar 29
  fis''4 e''4 c''4 a'4 |  % bar 30
  g'8( b'8) d''2( fis''4) |  % bar 31
  g''2\downbow\f fis''8( g''8 a''8 g''8) |  % bar 32
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \override BarNumber.break-visibility = ##(#f #t #t)
    barNumberVisibility = #all-bar-numbers-visible
  }
}
}
