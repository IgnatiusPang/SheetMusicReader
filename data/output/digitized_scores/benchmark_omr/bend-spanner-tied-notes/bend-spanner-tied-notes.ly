\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Bend Spanner Tied Notes"
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
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  a''4( a''4)( a''4) b''4 |  % bar 1
  a''4( a''4)( a''4) b''4 |  % bar 2
  a''4( a''4)( a''4) b''4 |  % bar 3
  c''2 d''2 |  % bar 4
  d''2( d''2) |  % bar 5
  c''2 \grace c''8 d''2( |  % bar 6
  d''2)( d''2) |  % bar 7
  c''2 r2 |  % bar 8
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
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  a''4( a''4)( a''4) b''4 |  % bar 1
  a''4( a''4)( a''4) b''4 |  % bar 2
  a''4( a''4)( a''4) b''4 |  % bar 3
  c''2 d''2 |  % bar 4
  d''2( d''2) |  % bar 5
  c''2 \grace c''8 d''2( |  % bar 6
  d''2)( d''2) |  % bar 7
  c''2 r2 |  % bar 8
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
