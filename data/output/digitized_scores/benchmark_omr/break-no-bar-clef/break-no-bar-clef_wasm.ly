\version "2.26.0"
\header {
  title = "break-no-bar-clef"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble c'2 \bar "|"
    c'2 \bar "|"
    \clef bass c'2 \bar "|"
    \clef treble c'2 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
