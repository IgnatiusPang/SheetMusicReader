\version "2.26.0"
\header {
  title = "dynamics-alignment-breaker"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble c'1 \bar "|"
    c'1 \bar "|"
    a1 \bar "|"
    c'1 \bar "|"
    \break
    c'1 \bar "|"
    a1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
