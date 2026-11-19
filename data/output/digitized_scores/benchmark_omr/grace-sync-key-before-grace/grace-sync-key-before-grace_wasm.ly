\version "2.26.0"
\header {
  title = "grace-sync-key-before-grace"
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
      \time 4/4 \key c \major \clef treble c''1 \bar "|"
      e''8 d''1 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key c \major \clef treble c'1 \bar "|"
      d'1 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
