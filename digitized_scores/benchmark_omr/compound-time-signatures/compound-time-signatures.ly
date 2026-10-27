\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Compound Time Signatures"
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
  \numericTimeSignature \clef treble \key bes \major \time 9/8
  % system 1
  \set Timing.measureLength = #5/4 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #9/8  % bar 1
  \set Timing.measureLength = #5/4 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #9/8  % bar 2
  \break
  % system 2
  \key c \major \time 4/4 c'8[ c'8 c'8 c'8 c'8 c'8] r4 |  % bar 3
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] r4 |  % bar 4
  \break
  % system 3
  \key ees \major \time 9/8 \set Timing.measureLength = #7/4 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #9/8  % bar 5
  \break
  % system 4
  \key c \major \set Timing.measureLength = #27/16 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #9/8  % bar 6
  \break
  % system 5
  \key ees \major \set Timing.measureLength = #19/8 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #9/8  % bar 7
  \break
  % system 6
  \key c \major \set Timing.measureLength = #9/4 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #9/8  % bar 8
  \break
  % system 7
  \key bes \major \set Timing.measureLength = #5/4 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #9/8  % bar 9
  \set Timing.measureLength = #5/4 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #9/8  % bar 10
  \break
  % system 8
  \key f \major c'8[ c'8 c'8 c'8] r2 r8 |  % bar 11
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16] r2 r8 |  % bar 12
  \break
  % system 9
  c'8[ c'8 c'8 c'8] r2 r8 |  % bar 13
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16] r2 r8 |  % bar 14
  \break
  % system 10
  \time 4/4 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] |  % bar 15
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] |  % bar 16
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
  \numericTimeSignature \clef treble \key bes \major \time 9/8
  % system 1
  \set Timing.measureLength = #5/4 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #9/8  % bar 1
  \set Timing.measureLength = #5/4 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #9/8  % bar 2
  \break
  % system 2
  \key c \major \time 4/4 c'8[ c'8 c'8 c'8 c'8 c'8] r4 |  % bar 3
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] r4 |  % bar 4
  \break
  % system 3
  \key ees \major \time 9/8 \set Timing.measureLength = #7/4 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #9/8  % bar 5
  \break
  % system 4
  \key c \major \set Timing.measureLength = #27/16 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #9/8  % bar 6
  \break
  % system 5
  \key ees \major \set Timing.measureLength = #19/8 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #9/8  % bar 7
  \break
  % system 6
  \key c \major \set Timing.measureLength = #9/4 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #9/8  % bar 8
  \break
  % system 7
  \key bes \major \set Timing.measureLength = #5/4 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] | \set Timing.measureLength = #9/8  % bar 9
  \set Timing.measureLength = #5/4 c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] | \set Timing.measureLength = #9/8  % bar 10
  \break
  % system 8
  \key f \major c'8[ c'8 c'8 c'8] r2 r8 |  % bar 11
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16] r2 r8 |  % bar 12
  \break
  % system 9
  c'8[ c'8 c'8 c'8] r2 r8 |  % bar 13
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16] r2 r8 |  % bar 14
  \break
  % system 10
  \time 4/4 c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] |  % bar 15
  c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] |  % bar 16
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
