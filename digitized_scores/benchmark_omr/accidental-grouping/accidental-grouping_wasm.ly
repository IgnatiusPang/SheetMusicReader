\version "2.26.0"
\header {
  title = "accidental-grouping"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key a \major \clef treble e'1 \bar "|"
    eis'1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
