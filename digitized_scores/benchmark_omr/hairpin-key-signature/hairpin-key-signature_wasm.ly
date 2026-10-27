\version "2.26.0"
\header {
  title = "hairpin-key-signature"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key a \major \clef treble c''4 c''4 c''4 c''4 \bar "|"
    c''4 c''4 c''4 c''4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
