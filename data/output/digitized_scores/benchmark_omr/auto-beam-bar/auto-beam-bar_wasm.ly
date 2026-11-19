\version "2.26.0"
\header {
  title = "auto-beam-bar"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 1/4 \key c \major \clef treble c'8[ c'8 c'8] \bar "|"
    c'8[ c'8 c'8 c'16 c'16 c'16 c'16 c'16 c'16] \bar "|"
    c'8[ c'8 c'8] \bar "|"
    c'16[ c'16 c'16 c'16 c'16 c'16] \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
