\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Chord Changes"
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
  \numericTimeSignature \clef treble \key f \major \time 2/4
  % system 1
  r2 |  % bar 1
  \break
  % system 2
  \time 4/8 r2 |  % bar 2
  \set Timing.measureLength = #1 <g'' ees'' c''>1 | \set Timing.measureLength = #1/2  % bar 3
  r2 |  % bar 4
  r2 |  % bar 5
  r2 |  % bar 6
  \break
  % system 3
  r2 |  % bar 7
  \set Timing.measureLength = #1 <g'' ees'' c''>1 | \set Timing.measureLength = #1/2  % bar 8
  r2 |  % bar 9
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
  \numericTimeSignature \clef treble \key f \major \time 2/4
  % system 1
  r2 |  % bar 1
  \break
  % system 2
  \time 4/8 r2 |  % bar 2
  \set Timing.measureLength = #1 <g'' ees'' c''>1 | \set Timing.measureLength = #1/2  % bar 3
  r2 |  % bar 4
  r2 |  % bar 5
  r2 |  % bar 6
  \break
  % system 3
  r2 |  % bar 7
  \set Timing.measureLength = #1 <g'' ees'' c''>1 | \set Timing.measureLength = #1/2  % bar 8
  r2 |  % bar 9
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
