\version "2.26.0"
\header {
  title = "clef-warn"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble <d' b>1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
