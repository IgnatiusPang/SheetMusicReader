\version "2.26.0"
\header {
  title = "auto-beam-ossia"
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
      \time 1/4 \key c \major \clef treble c'8 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 1/4 \key c \major \clef treble r2 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
