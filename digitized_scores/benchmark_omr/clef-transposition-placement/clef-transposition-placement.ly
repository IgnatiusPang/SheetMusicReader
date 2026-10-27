\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Clef Transposition Placement"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
  ragged-last = ##f
  system-system-spacing.basic-distance = #16
}
\score {
\new StaffGroup <<
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 16/16
  % system 1
  <c' g>1 |  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 16/16
  % system 1
  <c' g>1 |  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 16/16
  % system 1
  r1 |  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 16/16
  % system 1
  \set Timing.measureLength = #3/2 r1 r2 | \set Timing.measureLength = #1  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef bass \key c \major \time 16/16
  % system 1
  \set Timing.measureLength = #6 r1. r1. r1. f1. | \set Timing.measureLength = #1  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef bass \key c \major \time 16/16
  % system 1
  \set Timing.measureLength = #15/2 g1.\fermata r1.\fermata r1. r1. r1. | \set Timing.measureLength = #1  % bar 1
  \bar "|."
}
>>
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    
  }
}
}
\score {
\new StaffGroup <<
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 16/16
  % system 1
  <c' g>1 |  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 16/16
  % system 1
  <c' g>1 |  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 16/16
  % system 1
  r1 |  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 16/16
  % system 1
  \set Timing.measureLength = #3/2 r1 r2 | \set Timing.measureLength = #1  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef bass \key c \major \time 16/16
  % system 1
  \set Timing.measureLength = #6 r1. r1. r1. f1. | \set Timing.measureLength = #1  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef bass \key c \major \time 16/16
  % system 1
  \set Timing.measureLength = #15/2 g1.\fermata r1.\fermata r1. r1. r1. | \set Timing.measureLength = #1  % bar 1
  \bar "|."
}
>>
\midi { \tempo 4 = 90 }
}
