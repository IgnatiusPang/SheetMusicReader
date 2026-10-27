\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Accidental Tie"
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
  \numericTimeSignature \clef treble \key g \major \time 4/4
  % system 1
  f'1( |  % bar 1
  f'2)( fis'4) fis'8 gis'8( |  % bar 2
  \break
  % system 2
  gis'1) |  % bar 3
  f'1( |  % bar 4
  f'2)( fis'4) fis'8 gis'8( |  % bar 5
  \break
  % system 3
  g'1) |  % bar 6
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
  \numericTimeSignature \clef treble \key g \major \time 4/4
  % system 1
  f'1( |  % bar 1
  f'2)( fis'4) fis'8 gis'8( |  % bar 2
  \break
  % system 2
  gis'1) |  % bar 3
  f'1( |  % bar 4
  f'2)( fis'4) fis'8 gis'8( |  % bar 5
  \break
  % system 3
  g'1) |  % bar 6
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
