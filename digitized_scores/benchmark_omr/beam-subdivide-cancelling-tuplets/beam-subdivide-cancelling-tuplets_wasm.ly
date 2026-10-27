\version "2.26.0"
\header {
  title = "beam-subdivide-cancelling-tuplets"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 1/4 \key c \major \clef treble c'16[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'16] \bar "|"
    c'16[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'16] \bar "|"
    \clef alto d16[ d32 d32 d32 d32 d32 d32 d32 d32 d16] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
