\version "2.26.0"
\header {
  title = "accidental-fingering-collision"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble <cis' ais>4 <cis' ais>4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
