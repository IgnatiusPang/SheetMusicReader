\version "2.26.0"
\header {
  title = "dynamics-alignment-no-line"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble g'4 g'4 g'4 g'4 \bar "|"
    g1 \bar "|"
    g'4 g'4 g'4 g'4 \bar "|"
    g1 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
