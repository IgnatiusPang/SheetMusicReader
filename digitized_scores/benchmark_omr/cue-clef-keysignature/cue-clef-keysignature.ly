\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Cue Clef Keysignature"
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
  \numericTimeSignature \clef treble \key g \major \time 4/4
  % system 1
  g'4 g'4 g'4 g'4 |  % bar 1
  \clef bass c1 |  % bar 2
  \clef soprano g'4 g'4 g'4 g'4 |  % bar 3
  \break
  % system 2
  \clef bass d4 d4 d4 d4 |  % bar 4
  c1 |  % bar 5
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
  \numericTimeSignature \clef treble \key g \major \time 4/4
  % system 1
  g'4 g'4 g'4 g'4 |  % bar 1
  \clef bass c1 |  % bar 2
  \clef soprano g'4 g'4 g'4 g'4 |  % bar 3
  \break
  % system 2
  \clef bass d4 d4 d4 d4 |  % bar 4
  c1 |  % bar 5
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
