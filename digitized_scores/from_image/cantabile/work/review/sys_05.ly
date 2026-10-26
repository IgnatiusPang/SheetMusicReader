\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\paper { indent = 0 tagline = ##f line-width = 190\mm ragged-right = ##f }
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4 \set Score.currentBarNumber = #23
  % system 6
  d''4.\downbow( cis''8) d''4.\>( cis''8) |  % bar 23
  \set Timing.measureLength = #6/5 <>^\markup \with-color #red \bold "?" d''4( dis''4) eis''4( e''4)\! \grace c''8( c''4*4/5) | \set Timing.measureLength = #1  % bar 24
  b'4.( c''8) d''4( g''4) |  % bar 25
  g''2 fis''2\p |  % bar 26
  fis''4.( g''8) a''4( d''4) |  % bar 27
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \override BarNumber.break-visibility = ##(#f #t #t)
    barNumberVisibility = #all-bar-numbers-visible
  }
}
}
