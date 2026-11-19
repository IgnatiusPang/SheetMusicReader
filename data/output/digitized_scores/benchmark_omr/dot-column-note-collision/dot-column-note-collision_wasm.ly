\version "2.26.0"
\header {
  title = "dot-column-note-collision"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 3/4 \key c \major \clef treble f'4. g'4. f'4. \bar "|"
    g'4. a'4. \bar "|"
    b'16[ c''16] g'4. <f' b'>4. \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
