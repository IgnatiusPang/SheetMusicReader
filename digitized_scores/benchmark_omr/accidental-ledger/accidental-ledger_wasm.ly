\version "2.26.0"
\header {
  title = "accidental-ledger"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 1/8 \key c \major \clef treble r8 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
