\version "2.26.0"
\header {
  title = "auto-beam-recheck"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble a'8[ a'8 a'8 a'8 a'8 a'8 a'8 a'8] \bar "|"
    a'8[ a'8 a'8 a'16 a'16 a'8 a'8 a'16 a'16 a'8] \bar "|"
    r16 a'8. a'8[ a'16 a'16] r8. a'16[ a'8 a'16 a'16] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
