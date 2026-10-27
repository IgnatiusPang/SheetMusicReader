\version "2.26.0"
\header {
  title = "footnote-auto-numbering-page1"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble a4 b4 c'4 d'4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
