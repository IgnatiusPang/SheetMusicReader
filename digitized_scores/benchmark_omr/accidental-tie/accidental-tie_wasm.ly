\version "2.26.0"
\header {
  title = "accidental-tie"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key g \major \clef treble f'1 \bar "|"
    f'2 fis'4 fis'8[ gis'8] \bar "|"
    gis'1 \bar "|"
    f'1 \bar "|"
    \break
    f'2 fis'4 fis'8[ gis'8] \bar "|"
    g'1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
