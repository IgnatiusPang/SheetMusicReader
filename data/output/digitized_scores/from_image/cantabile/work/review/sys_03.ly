\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\paper { indent = 0 tagline = ##f line-width = 190\mm ragged-right = ##f }
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4 \set Score.currentBarNumber = #15
  % system 4
  a''8\downbow( fis''8) d''8( b'8) a'8( b'8) g'8( a'8) |  % bar 15
  fis'8( a'8) d''8( b'8) a'8( b'8) g'8( a'8) |  % bar 16
  fis'4( a'4) g'4( b'4) |  % bar 17
  d''4( fis''4) e''4( cis''4) |  % bar 18
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \override BarNumber.break-visibility = ##(#f #t #t)
    barNumberVisibility = #all-bar-numbers-visible
  }
}
}
