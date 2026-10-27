\version "2.26.0"
\header {
  title = "accidental-accent"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble f'8[ f'8 f'8 f'8] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
