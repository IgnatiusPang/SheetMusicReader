\version "2.26.0"
\header {
  title = "key-signature-space"
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
      \time 4/4 \key as \major \clef treble f'4 f'4 f'4 f'4 \bar "|"
      e''8[ e''8] e''4 e''2 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key as \major \clef treble r1 \bar "|"
      r1 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
