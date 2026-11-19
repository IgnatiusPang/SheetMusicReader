\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\paper { indent = 0 tagline = ##f line-width = 190\mm ragged-right = ##f }
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4 \set Score.currentBarNumber = #33
  % system 8
  g''2 fis''2 |  % bar 33
  c''2 b'8( c''8 d''8 c''8) |  % bar 34
  c''2 b'2 |  % bar 35
  g''2\downbow fis''8( g''8 a''8 g''8) |  % bar 36
  d''8( b'8) a'8( g'8) b'8( g'8) e'8( d'8) |  % bar 37
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \override BarNumber.break-visibility = ##(#f #t #t)
    barNumberVisibility = #all-bar-numbers-visible
  }
}
}
