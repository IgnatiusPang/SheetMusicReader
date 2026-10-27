\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Bar Number After Alternative Restore Grace"
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
  \set Timing.measureLength = #35/32 g'16. a'1\fermata | \set Timing.measureLength = #1  % bar 1
  b'1\fermata |  % bar 2
  \break
  % system 2
  \set Timing.measureLength = #35/32 g'16. a'1\fermata | \set Timing.measureLength = #1  % bar 3
  b'1\fermata |  % bar 4
  \break
  % system 3
  \set Timing.measureLength = #35/32 g'16. a'1 | \set Timing.measureLength = #1  % bar 5
  b'1\fermata |  % bar 6
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
  \set Timing.measureLength = #35/32 g'16. a'1\fermata | \set Timing.measureLength = #1  % bar 1
  b'1\fermata |  % bar 2
  \break
  % system 2
  \set Timing.measureLength = #35/32 g'16. a'1\fermata | \set Timing.measureLength = #1  % bar 3
  b'1\fermata |  % bar 4
  \break
  % system 3
  \set Timing.measureLength = #35/32 g'16. a'1 | \set Timing.measureLength = #1  % bar 5
  b'1\fermata |  % bar 6
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
