\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Grace Sync Time Signature"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
  ragged-last = ##f
  system-system-spacing.basic-distance = #16
}
\score {
\new PianoStaff <<
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  \set Timing.measureLength = #1 c'1 | \set Timing.measureLength = #3/4  % bar 1
  \grace e'8 d'4 e'4 f'4 |  % bar 2
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  \set Timing.measureLength = #1 c'1 | \set Timing.measureLength = #3/4  % bar 1
  d'4 e'4 f'4 |  % bar 2
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
\new PianoStaff <<
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  \set Timing.measureLength = #1 c'1 | \set Timing.measureLength = #3/4  % bar 1
  \grace e'8 d'4 e'4 f'4 |  % bar 2
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 3/4
  % system 1
  \set Timing.measureLength = #1 c'1 | \set Timing.measureLength = #3/4  % bar 1
  d'4 e'4 f'4 |  % bar 2
  \bar "|."
}
>>
\midi { \tempo 4 = 90 }
}
