\version "2.26.0"
\header {
  title = "bar-number-after-alternative-restore-grace"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble g'16. a'1 \bar "|"
    b'1 \bar "|"
    g'16. a'1 \bar "|"
    b'1 \bar "|"
    \break
    g'16. a'1 \bar "|"
    b'1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
