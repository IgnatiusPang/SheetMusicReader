\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Key Signature Space"
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
  \numericTimeSignature \clef treble \key aes \major \time 4/4
  % system 1
  f'4 f'4 f'4 f'4 |  % bar 1
  \key b \major e''8[ e''8] e''4 e''2 |  % bar 2
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key aes \major \time 4/4
  % system 1
  r1 |  % bar 1
  \key b \major r1 |  % bar 2
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
  \numericTimeSignature \clef treble \key aes \major \time 4/4
  % system 1
  f'4 f'4 f'4 f'4 |  % bar 1
  \key b \major e''8[ e''8] e''4 e''2 |  % bar 2
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key aes \major \time 4/4
  % system 1
  r1 |  % bar 1
  \key b \major r1 |  % bar 2
  \bar "|."
}
>>
\midi { \tempo 4 = 90 }
}
