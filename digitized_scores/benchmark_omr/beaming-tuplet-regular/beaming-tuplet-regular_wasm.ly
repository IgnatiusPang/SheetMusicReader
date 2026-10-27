\version "2.26.0"
\header {
  title = "beaming-tuplet-regular"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble b4*1/6[ b4*1/6 b4*1/6 b8 b8 b4*1/6 b4*1/6 b4*1/6 b4*1/6 b4*1/6 b4*1/6] b8. b8. b4*1/6[ b4*1/6 b4*1/6] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
