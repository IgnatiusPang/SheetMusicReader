\version "2.26.0"
\header {
  title = "dynamics-alignment-breaker-order"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble g1 \bar "|"
    c''1 \bar "|"
    c'1 \bar "|"
    f1 \bar "|"
    \break
    c1 \bar "|"
    c''1 \bar "|"
    c'1 \bar "|"
    f1 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
