\version "2.26.0"
\header {
  title = "dot-column-rest-collision"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble << { <e'' e>8[ e''8 g''8 g''8 <g'' c'>16] r8. <c'' a'>8. <g'' e'>16 } \\ { r8 r4. r2 } >> \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
