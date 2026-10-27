\version "2.26.0"
\header {
  title = "approximate-pitch-chord-repeat"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble d''2 d''2 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
