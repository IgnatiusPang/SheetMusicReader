\version "2.26.0"
\header {
  title = "accidental-broken-tie-spacing"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key bes \major \clef treble r1 \bar "|"
    ees''4 r2 ees''4 \bar "|"
    ees''4 r2 f''4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
