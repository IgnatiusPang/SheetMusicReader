\version "2.26.0"
\header {
  title = "laissez-vibrer-tie-beam"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble c'8[ e'8 g'8 c''8] r2 \bar "|"
    c'8[ e'8 g'8 c''8] r2 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
