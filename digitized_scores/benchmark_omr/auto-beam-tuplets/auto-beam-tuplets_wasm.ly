\version "2.26.0"
\header {
  title = "auto-beam-tuplets"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble f'4*1/3[ f'4*1/3 f'4*1/3 f'4*1/3 f'4*1/3 f'4*1/3 f'4*1/3 f'4*1/3 f'4*1/3 f'4*1/3 f'4*1/3 f'4*1/3] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
