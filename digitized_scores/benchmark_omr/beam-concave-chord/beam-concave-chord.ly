\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Beam Concave Chord"
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
  \numericTimeSignature \clef treble \key ees \major \time 2/4
  % system 1
  r2 |  % bar 1
  \time 5/8 c''16[ bes'16 c''16 ees''16 g''16 <ees'' bes''>16] r4 |  % bar 2
  c''16[ bes'16 c''16 ees''16 g''16 <ees'' bes''>16] r4 |  % bar 3
  \time 2/4 r2 |  % bar 4
  \break
  % system 2
  \set Timing.measureLength = #1 c'''8[ <g'' g' c''>8 <f'' c''>8 <ees'' ees'>8( <ees'' ees'>8) <c'' c'>8 <des'' des'>8 <des'' des'>8] | \set Timing.measureLength = #1/2  % bar 5
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
  \numericTimeSignature \clef treble \key ees \major \time 2/4
  % system 1
  r2 |  % bar 1
  \time 5/8 c''16[ bes'16 c''16 ees''16 g''16 <ees'' bes''>16] r4 |  % bar 2
  c''16[ bes'16 c''16 ees''16 g''16 <ees'' bes''>16] r4 |  % bar 3
  \time 2/4 r2 |  % bar 4
  \break
  % system 2
  \set Timing.measureLength = #1 c'''8[ <g'' g' c''>8 <f'' c''>8 <ees'' ees'>8( <ees'' ees'>8) <c'' c'>8 <des'' des'>8 <des'' des'>8] | \set Timing.measureLength = #1/2  % bar 5
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
