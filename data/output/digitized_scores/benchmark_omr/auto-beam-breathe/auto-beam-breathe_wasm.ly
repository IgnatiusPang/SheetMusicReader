\version "2.26.0"
\header {
  title = "auto-beam-breathe"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 1/1 \key c \major \clef treble c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
    c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
