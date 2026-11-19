\version "2.26.0"
\header {
  title = "grace-slashed-no-slur"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble c'16 c'1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
