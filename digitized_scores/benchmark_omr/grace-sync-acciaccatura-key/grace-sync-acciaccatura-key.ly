\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Grace Sync Acciaccatura Key"
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
  \numericTimeSignature \clef treble \key c \major \time 6/4
  % system 1
  c''2 r2 \grace d''8( c''2) |  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 6/4
  % system 1
  r2 c'2 c'2 |  % bar 1
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
  \numericTimeSignature \clef treble \key c \major \time 6/4
  % system 1
  c''2 r2 \grace d''8( c''2) |  % bar 1
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 6/4
  % system 1
  r2 c'2 c'2 |  % bar 1
  \bar "|."
}
>>
\midi { \tempo 4 = 90 }
}
