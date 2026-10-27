\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Footnote Auto Numbering Page2"
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
  a1 |  % bar 1
  \break
  % system 2
  d'4 e'4 <f' c'' a'>4 a'8[ b'8] |  % bar 2
  c''8[ d''8] a'4 b'4 c''4 |  % bar 3
  d'1 |  % bar 4
  \break
  % system 3
  \key c \major d''4 a'4 b'4 c''4 |  % bar 5
  d''4 a'4 b'4 c''4 |  % bar 6
  d''4 a'4 b'4 c''4 |  % bar 7
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
  a1 |  % bar 1
  \break
  % system 2
  d'4 e'4 <f' c'' a'>4 a'8[ b'8] |  % bar 2
  c''8[ d''8] a'4 b'4 c''4 |  % bar 3
  d'1 |  % bar 4
  \break
  % system 3
  \key c \major d''4 a'4 b'4 c''4 |  % bar 5
  d''4 a'4 b'4 c''4 |  % bar 6
  d''4 a'4 b'4 c''4 |  % bar 7
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
