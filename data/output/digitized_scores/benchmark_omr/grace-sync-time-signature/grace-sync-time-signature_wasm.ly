\version "2.26.0"
\header {
  title = "grace-sync-time-signature"
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
      \time 3/4 \key c \major \clef treble c'1 \bar "|"
      e'8 d'4 e'4 f'4 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 3/4 \key c \major \clef treble c'1 \bar "|"
      d'4 e'4 f'4 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
