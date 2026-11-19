\version "2.26.0"
\header {
  title = "accidental-unbroken-tie-spacing"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 3/4 \key c \major \clef treble c'8 b2 <g f' des' b>8 \bar "|"
    <g f' des' b>8 r8 \clef alto b4 b4 \bar "|"
    b4 b4 b4 \bar "|"
    b4 b4 \clef alto b4 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
