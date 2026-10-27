\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Accidental Contemporary"
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
  gis'4 a'4 gis'4 g'4 |  % bar 1
  gis'8 a'8 gis'8 gis'8 g''8 gis''8 gis8 a'8 |  % bar 2
  eis'8 fis'8 eis'8 eis'8 gis'2 |  % bar 3
  \key a \major \time 8/8 \set Timing.measureLength = #1/4 r4 | \set Timing.measureLength = #1  % bar 4
  \break
  % system 2
  \key e \major e'8 eis'8 fis'8 fis'8 gis'2 |  % bar 5
  \break
  % system 3
  \time 4/4 gis'4 a'4 gis'4 g'4 |  % bar 6
  gis'8 a'8 gis'8 gis'8 g''8 gis''8 gis8 a'8 |  % bar 7
  eis'8 fis'8 eis'8 eis'8 g'2 |  % bar 8
  \break
  % system 4
  \key a \major \time 8/8 \set Timing.measureLength = #5/4 r4 e'8 eis'8 fis'8 fis'8 gis'2 | \set Timing.measureLength = #1  % bar 9
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
  gis'4 a'4 gis'4 g'4 |  % bar 1
  gis'8 a'8 gis'8 gis'8 g''8 gis''8 gis8 a'8 |  % bar 2
  eis'8 fis'8 eis'8 eis'8 gis'2 |  % bar 3
  \key a \major \time 8/8 \set Timing.measureLength = #1/4 r4 | \set Timing.measureLength = #1  % bar 4
  \break
  % system 2
  \key e \major e'8 eis'8 fis'8 fis'8 gis'2 |  % bar 5
  \break
  % system 3
  \time 4/4 gis'4 a'4 gis'4 g'4 |  % bar 6
  gis'8 a'8 gis'8 gis'8 g''8 gis''8 gis8 a'8 |  % bar 7
  eis'8 fis'8 eis'8 eis'8 g'2 |  % bar 8
  \break
  % system 4
  \key a \major \time 8/8 \set Timing.measureLength = #5/4 r4 e'8 eis'8 fis'8 fis'8 gis'2 | \set Timing.measureLength = #1  % bar 9
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
