\version "2.26.0"
\header {
  title = "dynamics-alignment-no-line-linebreak"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble c''2 g2 \bar "|"
    g2 c''2 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
