\version "2.26.0"
\header {
  title = "alternating-time-beam-exceptions"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new PianoStaff <<
    \new Staff {
      \accidentalStyle modern
      \time 2/2 \key f \major \clef treble c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
      c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
      c'8[ c'8 c'8] r2 r8 \bar "|"
      c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] r16 \bar "|"
      \break
      c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] \bar "|"
      c'16[ c'16 c'16 c'16 c'16 c'16 c'16] r2 r16 \bar "|"
      c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] \bar "|"
      c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] \bar "|"
      \break
      c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] r2 r32 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 2/2 \key f \major \clef treble c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
      c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
      c'8[ c'8 c'8] r2 r8 \bar "|"
      c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] r16 \bar "|"
      \break
      c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] \bar "|"
      c'16[ c'16 c'16 c'16 c'16 c'16 c'16] r2 r16 \bar "|"
      c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] \bar "|"
      c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 <c' c'>32 <c' c'>32] \bar "|"
      \break
      c'32[ c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32 c'32] r2 r32 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
