\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Accidental Broken Tie Spacing"
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
  \numericTimeSignature \clef treble \key bes \major \time 4/4
  % system 1
  r1 |  % bar 1
  \break
  % system 2
  ees''4 r2 ees''4( |  % bar 2
  \break
  % system 3
  ees''4) r2 f''4 |  % bar 3
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
  \numericTimeSignature \clef treble \key bes \major \time 4/4
  % system 1
  r1 |  % bar 1
  \break
  % system 2
  ees''4 r2 ees''4( |  % bar 2
  \break
  % system 3
  ees''4) r2 f''4 |  % bar 3
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
