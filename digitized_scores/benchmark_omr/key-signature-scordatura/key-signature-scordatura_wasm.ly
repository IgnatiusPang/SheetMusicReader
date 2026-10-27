\version "2.26.0"
\header {
  title = "key-signature-scordatura"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 1/4 \key g \major \clef treble f'8[ a'8 c''8 e''8] \bar "|"
    r8 r8 r8 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
