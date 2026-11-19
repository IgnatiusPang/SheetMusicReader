\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Chord Repetition Times"
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
  \numericTimeSignature \clef treble \key c \major \time 2/4
  % system 1
  \set Timing.measureLength = #1 <g' e' c'>4 r4 <g' d' b>2( | \set Timing.measureLength = #1/2  % bar 1
  \set Timing.measureLength = #5969/12320 <g' d' c'>4*4/5) g'8*8/11[ g'8*8/11 d'16*4/7 g'16*4/7] r32 | \set Timing.measureLength = #1/2  % bar 2
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
  \numericTimeSignature \clef treble \key c \major \time 2/4
  % system 1
  \set Timing.measureLength = #1 <g' e' c'>4 r4 <g' d' b>2( | \set Timing.measureLength = #1/2  % bar 1
  \set Timing.measureLength = #5969/12320 <g' d' c'>4*4/5) g'8*8/11[ g'8*8/11 d'16*4/7 g'16*4/7] r32 | \set Timing.measureLength = #1/2  % bar 2
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
