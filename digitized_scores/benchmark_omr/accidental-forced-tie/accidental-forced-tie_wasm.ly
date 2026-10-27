\version "2.26.0"
\header {
  title = "accidental-forced-tie"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble gis'4 gis'4 gis'4 r4 \bar "|"
    fis'1 \bar "|"
    fis'2 fis'2 \bar "|"
    fis'2 fis'2 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
