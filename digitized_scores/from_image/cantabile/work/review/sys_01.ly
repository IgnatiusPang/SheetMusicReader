\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\paper { indent = 0 tagline = ##f line-width = 190\mm ragged-right = ##f }
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4 \set Score.currentBarNumber = #6
  % system 2
  d''4.( b'8) d''8( c''8 a'8 d''8) |  % bar 6
  d''4( b'4) c''4( e''4) |  % bar 7
  g'2 fis'2 |  % bar 8
  b'4.\downbow\p( c''8) d''4( g''4) |  % bar 9
  g''2 fis''2 |  % bar 10
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \override BarNumber.break-visibility = ##(#f #t #t)
    barNumberVisibility = #all-bar-numbers-visible
  }
}
}
