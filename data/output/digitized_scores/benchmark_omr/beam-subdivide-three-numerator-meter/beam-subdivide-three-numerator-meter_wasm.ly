\version "2.26.0"
\header {
  title = "beam-subdivide-three-numerator-meter"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/8 \key c \major \clef treble c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] \bar "|"
    \clef alto d32[ d32 d32 d32 d32 d32 d32 d32 d32 d32 d32 d32] \bar "|"
    \clef treble d8. d16 \bar "|"
    d16[ d8] r16 \bar "|"
    \break
    \clef alto f32[ d32 d32 d32 d32 d32 d32 d32 d32 d32 d32 d32] r8 \bar "|"
    \clef treble d16.[ d32] r4. \bar "|"
    d32[ d16] r4. r32 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
