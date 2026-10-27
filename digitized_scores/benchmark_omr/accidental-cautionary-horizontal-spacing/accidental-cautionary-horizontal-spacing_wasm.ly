\version "2.26.0"
\header {
  title = "accidental-cautionary-horizontal-spacing"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble c'8[ cis'8 cis'8 cis'8 f'8 fis'8 g'8] fis'8 fis'8 \bar "|"
    c'8[ cis'8 cis'8 cis'8 f'8 fis'8 g'8] fis'8 fis'8 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
