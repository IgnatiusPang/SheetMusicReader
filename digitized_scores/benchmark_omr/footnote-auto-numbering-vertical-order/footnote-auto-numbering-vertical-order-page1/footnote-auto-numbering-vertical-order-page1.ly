\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Footnote Auto Numbering Vertical Order Page1"
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
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  d'4 e'4 <f' c'' a'>4( a'8)[ b'8] |  % bar 1
  c''8[ d''8] a'4 b'4 c''4 |  % bar 2
  d''4 a'4 b'4 c''4 |  % bar 3
  \break
  % system 2
  d'4 e'4 <f' c'' a'>4( a'8)[ b'8] |  % bar 4
  c''8[ d''8] a'4 b'4 c''4 |  % bar 5
  d''4 a'4 b'4 c''4 |  % bar 6
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  d'4 e'4 <f' c'' a'>4( a'8[ b'8] |  % bar 1
  c''4 a'4 b'4 c''4 |  % bar 2
  d''4 a'4 b'4 c''4 |  % bar 3
  \break
  % system 2
  d'4 e'4 <f' c'' a'>4 a'8[ b'8] |  % bar 4
  c''4 a'4 b'4 c''4 |  % bar 5
  d''4 a'4 b'4 c''4) |  % bar 6
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
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  d'4 e'4 <f' c'' a'>4( a'8)[ b'8] |  % bar 1
  c''8[ d''8] a'4 b'4 c''4 |  % bar 2
  d''4 a'4 b'4 c''4 |  % bar 3
  \break
  % system 2
  d'4 e'4 <f' c'' a'>4( a'8)[ b'8] |  % bar 4
  c''8[ d''8] a'4 b'4 c''4 |  % bar 5
  d''4 a'4 b'4 c''4 |  % bar 6
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  d'4 e'4 <f' c'' a'>4( a'8[ b'8] |  % bar 1
  c''4 a'4 b'4 c''4 |  % bar 2
  d''4 a'4 b'4 c''4 |  % bar 3
  \break
  % system 2
  d'4 e'4 <f' c'' a'>4 a'8[ b'8] |  % bar 4
  c''4 a'4 b'4 c''4 |  % bar 5
  d''4 a'4 b'4 c''4) |  % bar 6
  \bar "|."
}
>>
\midi { \tempo 4 = 90 }
}
