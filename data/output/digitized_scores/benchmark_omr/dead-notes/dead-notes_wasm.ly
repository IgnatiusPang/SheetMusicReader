\version "2.26.0"
\header {
  title = "dead-notes"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef bass e,8. e,16 g,4 a,4 b,4 \bar "|"
    e8. e16 g4 a4 b4 \bar "|"
    e4. e8[ e8 e8] e4 \bar "|"
    <e e,>8[ <e e,>8] <e e,>4 <e e,>4 r4 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
