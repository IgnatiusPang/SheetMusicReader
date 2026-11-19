\version "2.26.0"
\header {
  title = "beam-rest"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef bass e,8 r16 f,16[ d8 e16 e16] c4 c16 r16 bes,8 r16 c16 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
