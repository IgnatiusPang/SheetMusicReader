\version "2.26.0"
\header {
  title = "compound-time-signatures"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 9/8 \key bes \major \clef treble c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
    c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] \bar "|"
    c'8[ c'8 c'8 c'8 c'8 c'8] r4 \bar "|"
    c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] r4 \bar "|"
    \break
    c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
    c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] \bar "|"
    c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
    c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] \bar "|"
    \break
    c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
    c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] \bar "|"
    c'8[ c'8 c'8 c'8] r2 r8 \bar "|"
    c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16] r2 r8 \bar "|"
    \break
    c'8[ c'8 c'8 c'8] r2 r8 \bar "|"
    c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16] r2 r8 \bar "|"
    c'8[ c'8 c'8 c'8 c'8 c'8 c'8 c'8] \bar "|"
    c'16[ c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16] \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
