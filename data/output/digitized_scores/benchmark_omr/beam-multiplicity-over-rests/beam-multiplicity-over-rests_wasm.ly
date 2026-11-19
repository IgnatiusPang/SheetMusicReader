\version "2.26.0"
\header {
  title = "beam-multiplicity-over-rests"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 3/4 \key c \major \clef treble c'8 r16 c'32[ c'32 c'32] r16 c'32[ c'8 c'32 c'32] r16. c'32[ c'32 c'16. c'32 c'32 c'32] r16 c'8 \bar "|"
    c'16 r32 c'32 r16 c'16[ c'16] r16 c'32 r32 c'16 r4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
