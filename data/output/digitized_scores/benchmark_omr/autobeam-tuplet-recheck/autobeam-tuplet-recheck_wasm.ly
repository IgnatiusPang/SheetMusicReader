\version "2.26.0"
\header {
  title = "autobeam-tuplet-recheck"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble c'16[ c'16 c'8 c'16 c'8 c'16 c'16 c'16] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
