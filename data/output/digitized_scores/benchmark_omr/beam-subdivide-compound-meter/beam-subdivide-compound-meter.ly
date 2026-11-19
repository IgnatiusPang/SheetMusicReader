\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Beam Subdivide Compound Meter"
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
  \numericTimeSignature \clef alto \key f \major \time 2/4
  % system 1
  \set Timing.measureLength = #11/16 f'32[ f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32] | \set Timing.measureLength = #1/2  % bar 1
  \break
  % system 2
  \clef treble \key c \major \set Timing.measureLength = #21/32 e''32[ e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32] | \set Timing.measureLength = #1/2  % bar 2
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
  \numericTimeSignature \clef alto \key f \major \time 2/4
  % system 1
  \set Timing.measureLength = #11/16 f'32[ f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32] | \set Timing.measureLength = #1/2  % bar 1
  \break
  % system 2
  \clef treble \key c \major \set Timing.measureLength = #21/32 e''32[ e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32] | \set Timing.measureLength = #1/2  % bar 2
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
