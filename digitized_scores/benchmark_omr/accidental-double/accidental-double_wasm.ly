\version "2.26.0"
\header {
  title = "accidental-double"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key g \major \clef treble <c'' c'>4 fis'4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
