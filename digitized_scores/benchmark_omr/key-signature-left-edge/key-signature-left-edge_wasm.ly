\version "2.26.0"
\header {
  title = "key-signature-left-edge"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 1/4 \key f \major \clef treble c'8 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
