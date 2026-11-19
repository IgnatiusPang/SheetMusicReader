\version "2.26.0"
\header {
  title = "chord-changes-alternative"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble g'4 f'4 e'4 d'4 \bar "|"
    c'4 r4 r4 r4 \bar "|"
    c'4 g4 c'4 r4 \bar "|"
    b4 g4 c'2 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
