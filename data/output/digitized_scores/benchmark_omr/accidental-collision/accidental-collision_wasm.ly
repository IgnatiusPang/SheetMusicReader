\version "2.26.0"
\header {
  title = "accidental-collision"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 1/4 \key c \major \clef treble a''16 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
