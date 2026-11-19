\version "2.26.0"
\header {
  title = "accidental-ancient"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 3/4 \key c \major \clef treble cis''4 cis''4 ces''4 \bar "|"
    c''4 c''4 ces''4 \bar "|"
    c''4 c''4 ces''4 \bar "|"
    c''4 c''4 ces''4 \bar "|"
    \break
    c''4 c''4 ces''4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
