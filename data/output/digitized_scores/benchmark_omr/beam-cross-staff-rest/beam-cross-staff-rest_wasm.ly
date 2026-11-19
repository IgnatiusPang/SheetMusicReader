\version "2.26.0"
\header {
  title = "beam-cross-staff-rest"
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
      \time 4/8 \key c \major \clef treble a'2. \bar "|"
      c'''8 r16 fis''16 r16 r8. \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 4/8 \key c \major \clef treble r2. \bar "|"
      r8 c''16 r8 fis''16 r8 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
