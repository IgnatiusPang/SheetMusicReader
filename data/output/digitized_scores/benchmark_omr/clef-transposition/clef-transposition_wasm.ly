\version "2.26.0"
\header {
  title = "clef-transposition"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 3/4 \key c \major \clef treble c'''4 f'''4 b''4 a''4 \bar "|"
    c'4 b4 r4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
