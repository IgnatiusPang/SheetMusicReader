\version "2.26.0"
\header {
  title = "clef-transposition-optional"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef bass b,1 \bar "|"
    c1 \clef tenor a1 \bar "|"
    a1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
