\version "2.26.0"
\header {
  title = "autochange-after-rest"
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
      \time 4/4 \key c \major \clef treble r4 r2 d'4 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key c \major \clef bass r4 g4 c'4 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
