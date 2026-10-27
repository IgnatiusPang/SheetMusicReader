\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Beam Cross Staff Rest"
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
  \numericTimeSignature \clef treble \key c \major \time 4/8
  % system 1
  \set Timing.measureLength = #3/4 a'2. | \set Timing.measureLength = #1/2  % bar 1
  c'''8 r16 fis''16 r16 r8. |  % bar 2
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 4/8
  % system 1
  \set Timing.measureLength = #3/4 r2. | \set Timing.measureLength = #1/2  % bar 1
  r8 c''16 r8 fis''16 r8 |  % bar 2
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
  \numericTimeSignature \clef treble \key c \major \time 4/8
  % system 1
  \set Timing.measureLength = #3/4 a'2. | \set Timing.measureLength = #1/2  % bar 1
  c'''8 r16 fis''16 r16 r8. |  % bar 2
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 4/8
  % system 1
  \set Timing.measureLength = #3/4 r2. | \set Timing.measureLength = #1/2  % bar 1
  r8 c''16 r8 fis''16 r8 |  % bar 2
  \bar "|."
}
>>
\midi { \tempo 4 = 90 }
}
