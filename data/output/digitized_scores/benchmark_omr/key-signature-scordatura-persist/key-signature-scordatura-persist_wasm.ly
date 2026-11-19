\version "2.26.0"
\header {
  title = "key-signature-scordatura-persist"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key bes \major \clef treble f'4 f'4 a'4 bes'4 \bar "|"
    fis''4 a'4 a'4 bes'4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
