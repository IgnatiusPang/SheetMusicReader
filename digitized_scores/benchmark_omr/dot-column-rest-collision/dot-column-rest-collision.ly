\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Dot Column Rest Collision"
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
  << { <e'' e>8[ e''8 g''8 g''8 <g'' c'>16] r8. <c'' a'>8. <g'' e'>16 } \\ { r8 r4. r2 } >> |  % bar 1
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
  << { <e'' e>8[ e''8 g''8 g''8 <g'' c'>16] r8. <c'' a'>8. <g'' e'>16 } \\ { r8 r4. r2 } >> |  % bar 1
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
