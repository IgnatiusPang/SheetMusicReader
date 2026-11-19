\version "2.26.0"
\header {
  title = "auto-beam-beaming-override"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble b16[ b16 b16 b16 b16 b16 b16 b16] \bar "|"
    b16[ b16 b16 b16 b16 b16 b16 b16] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
