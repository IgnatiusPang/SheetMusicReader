\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Bar Number After Alternative Restore Cadenza"
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
  \numericTimeSignature \clef treble \key c \major \time 2/4 \partial 4
  % system 1
  r4\fermata |  % bar 1
  \set Timing.measureLength = #1 b'1\fermata | \set Timing.measureLength = #1/2  % bar 2
  \break
  % system 2
  r4\fermata r4 |  % bar 3
  \set Timing.measureLength = #1 b'1\fermata | \set Timing.measureLength = #1/2  % bar 4
  \break
  % system 3
  r4\fermata r4 |  % bar 5
  \set Timing.measureLength = #1 b'1\fermata | \set Timing.measureLength = #1/2  % bar 6
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
  \numericTimeSignature \clef treble \key c \major \time 2/4 \partial 4
  % system 1
  r4\fermata |  % bar 1
  \set Timing.measureLength = #1 b'1\fermata | \set Timing.measureLength = #1/2  % bar 2
  \break
  % system 2
  r4\fermata r4 |  % bar 3
  \set Timing.measureLength = #1 b'1\fermata | \set Timing.measureLength = #1/2  % bar 4
  \break
  % system 3
  r4\fermata r4 |  % bar 5
  \set Timing.measureLength = #1 b'1\fermata | \set Timing.measureLength = #1/2  % bar 6
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
