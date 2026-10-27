\version "2.26.0"
\header {
  title = "break-no-bar-key"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key es \major \clef treble c'2 \bar "|"
    c'2 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
