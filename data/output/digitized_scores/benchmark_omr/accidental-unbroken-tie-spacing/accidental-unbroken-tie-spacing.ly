\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Accidental Unbroken Tie Spacing"
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
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  c'8 b2 <g f' des' b>8( |  % bar 1
  <g f' des' b>8) r8 \clef soprano b4( b4)( |  % bar 2
  b4)( b4) b4( |  % bar 3
  \break
  % system 2
  \clef treble \key c \major b4)( b4) \clef soprano b4 |  % bar 4
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
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  c'8 b2 <g f' des' b>8( |  % bar 1
  <g f' des' b>8) r8 \clef soprano b4( b4)( |  % bar 2
  b4)( b4) b4( |  % bar 3
  \break
  % system 2
  \clef treble \key c \major b4)( b4) \clef soprano b4 |  % bar 4
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
