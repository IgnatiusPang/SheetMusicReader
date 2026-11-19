\version "2.26.0"
\header {
  title = "clef-transposition-visibility"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble c''2 c''2 \bar "|"
    c''2 c''2 \bar "|"
    c''2 \clef tenor c'2 \bar "|"
    b2 b2 \bar "|"
    \break
    b2 b2 \bar "|"
    c''2 c''2 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
