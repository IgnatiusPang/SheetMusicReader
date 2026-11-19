\version "2.26.0"
\header {
  title = "clef-ottava"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef alto a'4 b'4 c''4 a'4 \bar "|"
    a4 b4 c'4 a4 \bar "|"
    \clef bass a4 b4 c'4 a4 \bar "|"
    \clef alto a,4 b,4 c4 a,4 \bar "|"
    \break
    \clef treble a''4 b''4 c'''4 a''4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
