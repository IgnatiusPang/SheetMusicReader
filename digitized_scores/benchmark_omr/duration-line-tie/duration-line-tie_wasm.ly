\version "2.26.0"
\header {
  title = "duration-line-tie"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble a'1 \bar "|"
    g'1 \bar "|"
    g'1 \bar "|"
    f'1 \bar "|"
    \break
    a'1 \bar "|"
    a'1 \bar "|"
    g'1 \bar "|"
    f'1 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
