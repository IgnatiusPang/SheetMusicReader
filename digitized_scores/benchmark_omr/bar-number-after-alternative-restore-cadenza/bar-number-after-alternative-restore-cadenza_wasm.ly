\version "2.26.0"
\header {
  title = "bar-number-after-alternative-restore-cadenza"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble r4 \bar "|"
    b'1 \bar "|"
    r4 r4 \bar "|"
    b'1 \bar "|"
    \break
    r4 r4 \bar "|"
    b'1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
