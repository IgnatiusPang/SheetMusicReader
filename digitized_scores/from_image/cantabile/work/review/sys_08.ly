\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\paper { indent = 0 tagline = ##f line-width = 190\mm ragged-right = ##f }
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4 \set Score.currentBarNumber = #38
  % system 9
  g'8( d'8) c''8( b'8) d''8( b'8) a'8( g'8) |  % bar 38
  g'2\downbow\p fis'8( g'8 a'8 g'8) |  % bar 39
  g1( |  % bar 40
  g4) r4 r2 |  % bar 41
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \override BarNumber.break-visibility = ##(#f #t #t)
    barNumberVisibility = #all-bar-numbers-visible
  }
}
}
