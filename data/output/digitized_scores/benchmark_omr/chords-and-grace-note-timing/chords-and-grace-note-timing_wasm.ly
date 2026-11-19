\version "2.26.0"
\header {
  title = "chords-and-grace-note-timing"
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
      \time 4/4 \key c \major \clef treble c'4 c''1 \bar "|"
      c'4 c''1 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key c \major \clef treble c'1 \bar "|"
      c'1 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
