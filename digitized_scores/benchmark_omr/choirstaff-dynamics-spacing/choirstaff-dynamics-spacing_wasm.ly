\version "2.26.0"
\header {
  title = "choirstaff-dynamics-spacing"
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
      \time 4/4 \key c \major \clef treble c4 c4 c4 c4 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key c \major \clef treble c4 c4 c4 c4 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
