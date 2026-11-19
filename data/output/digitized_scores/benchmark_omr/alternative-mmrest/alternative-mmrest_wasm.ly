\version "2.26.0"
\header {
  title = "alternative-mmrest"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 3/4 \key c \major \clef treble c'4 \bar "|"
    c'1 \bar "|"
    c'2. \bar "|"
    r2. \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
