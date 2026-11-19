\version "2.26.0"
\header {
  title = "dynamics-avoid-cross-staff-stem"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble f'4 f'4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
