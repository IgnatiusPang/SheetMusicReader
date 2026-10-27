\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Fingering Adjacent Note Chord New"
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
  <c' e'>1 |  % bar 1
  <d'' b' a''>1 |  % bar 2
  <e'' e' d''>4 <fis'' b' a'>4 <e'' e' d''>4 <fis'' e'' eis'>4 |  % bar 3
  <e' d'' b'>1 |  % bar 4
  <e'' e' d''>4 <fis'' b' a'>4 <e'' e' d''>4 <fis'' e'' eis'>4 |  % bar 5
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
  <c' e'>1 |  % bar 1
  <d'' b' a''>1 |  % bar 2
  <e'' e' d''>4 <fis'' b' a'>4 <e'' e' d''>4 <fis'' e'' eis'>4 |  % bar 3
  <e' d'' b'>1 |  % bar 4
  <e'' e' d''>4 <fis'' b' a'>4 <e'' e' d''>4 <fis'' e'' eis'>4 |  % bar 5
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
