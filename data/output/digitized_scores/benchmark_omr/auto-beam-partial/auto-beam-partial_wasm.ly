\version "2.26.0"
\header {
  title = "auto-beam-partial"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/8 \key c \major \clef treble a'8[ a'8 a'8 a'8] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
