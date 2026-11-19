\version "2.26.0"
\header {
  title = "key-signature-padding"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key d \major \clef treble ges2 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
