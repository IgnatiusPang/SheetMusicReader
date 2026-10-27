\version "2.26.0"
\header {
  title = "completion-heads-tie"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble r2 d''2 \bar "|"
    d''2 d''2 \bar "|"
    d''2 d''2 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
