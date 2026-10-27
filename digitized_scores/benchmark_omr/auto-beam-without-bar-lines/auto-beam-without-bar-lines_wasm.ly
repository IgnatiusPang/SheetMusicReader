\version "2.26.0"
\header {
  title = "auto-beam-without-bar-lines"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 8/4 \key c \major \clef treble c'8[ c'8 d'8 d'8 d'8 d'8 d'8 d'8 e'8 e'8 e'8 e'8 f'8 f'8 g'8 g'8] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
