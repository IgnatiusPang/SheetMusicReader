\version "2.26.0"
\header {
  title = "grace-sync-acciaccatura-key"
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
      \time 6/4 \key c \major \clef treble c''2 r2 d''8 c''2 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 6/4 \key c \major \clef treble r2 c'2 c'2 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
