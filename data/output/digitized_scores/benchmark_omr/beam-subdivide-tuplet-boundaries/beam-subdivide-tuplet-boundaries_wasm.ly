\version "2.26.0"
\header {
  title = "beam-subdivide-tuplet-boundaries"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble c'16[ c'32 c'32 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'64 c'32 c'32 c'32 c'32] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
