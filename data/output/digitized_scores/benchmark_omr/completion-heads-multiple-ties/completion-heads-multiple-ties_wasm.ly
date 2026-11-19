\version "2.26.0"
\header {
  title = "completion-heads-multiple-ties"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble c'4*7/4 c'16 \bar "|"
    c'4 c'16 c'8. \bar "|"
    c'8. c'4 c'16 \bar "|"
    c'8. c'4 c'16 \bar "|"
    \break
    c'2 \bar "|"
    c'8. r4 r16 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
