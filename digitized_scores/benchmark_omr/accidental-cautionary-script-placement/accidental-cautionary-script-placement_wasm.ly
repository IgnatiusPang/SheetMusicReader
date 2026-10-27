\version "2.26.0"
\header {
  title = "accidental-cautionary-script-placement"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble c'''4 c'''4 ces'''8 c'''4 ces'''4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
