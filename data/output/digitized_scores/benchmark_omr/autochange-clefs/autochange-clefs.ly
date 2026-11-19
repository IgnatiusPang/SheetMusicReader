\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Autochange Clefs"
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
  \numericTimeSignature \clef soprano \key c \major \time 4/4
  % system 1
  r8 r4 c'8[ b8 d'8 c'8 e'8] |  % bar 1
  d'8 r8 f'8[ g'8] a'2 |  % bar 2
  \break
  % system 2
  \clef tenor r8 b8 r2 r8 e'8 |  % bar 3
  d'8 r8 d'8[ e'8] f'2 |  % bar 4
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef bass \key c \major \time 4/4 \partial 4.
  % system 1
  g8[ b8 a8] |  % bar 1
  b1 |  % bar 2
  \break
  % system 2
  g8 r8 a8[ c'8 b8 d'8 c'8] r8 |  % bar 3
  r1 |  % bar 4
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
  \numericTimeSignature \clef soprano \key c \major \time 4/4
  % system 1
  r8 r4 c'8[ b8 d'8 c'8 e'8] |  % bar 1
  d'8 r8 f'8[ g'8] a'2 |  % bar 2
  \break
  % system 2
  \clef tenor r8 b8 r2 r8 e'8 |  % bar 3
  d'8 r8 d'8[ e'8] f'2 |  % bar 4
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef bass \key c \major \time 4/4 \partial 4.
  % system 1
  g8[ b8 a8] |  % bar 1
  b1 |  % bar 2
  \break
  % system 2
  g8 r8 a8[ c'8 b8 d'8 c'8] r8 |  % bar 3
  r1 |  % bar 4
  \bar "|."
}
>>
\midi { \tempo 4 = 90 }
}
