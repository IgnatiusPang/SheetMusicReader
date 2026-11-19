\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\paper { indent = 0 tagline = ##f line-width = 190\mm ragged-right = ##f }
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4
  % system 1
  b'4.\downbow\p( c''8) d''4( g''4) |  % bar 1
  g''2 fis''2 |  % bar 2
  \set Timing.measureLength = #7/6 <>^\markup \with-color #red \bold "?" fis''2.( \tuplet 3/2 { g''8) a''4( } d''4*2/3) | \set Timing.measureLength = #1  % bar 3
  b''2( g''2) |  % bar 4
  d''4.( b'8) d''8( c''8 a'8 d''8) |  % bar 5
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \override BarNumber.break-visibility = ##(#f #t #t)
    barNumberVisibility = #all-bar-numbers-visible
  }
}
}
