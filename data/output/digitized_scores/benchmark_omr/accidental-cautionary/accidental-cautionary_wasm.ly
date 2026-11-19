\version "2.26.0"
\header {
  title = "accidental-cautionary"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble c''4 cis''4 cis''4 cis''4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
