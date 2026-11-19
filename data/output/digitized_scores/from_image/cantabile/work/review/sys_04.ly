\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\paper { indent = 0 tagline = ##f line-width = 190\mm ragged-right = ##f }
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4 \set Score.currentBarNumber = #19
  % system 5
  d''2\downbow cis''8( d''8 e''8 d''8) |  % bar 19
  cis''4( b''4) a''4( cis''4) |  % bar 20
  d''2\downbow cis''8( d''8 e''8 d''8) |  % bar 21
  cis''4( b''4) a''4( cis''4) |  % bar 22
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    \override BarNumber.break-visibility = ##(#f #t #t)
    barNumberVisibility = #all-bar-numbers-visible
  }
}
}
