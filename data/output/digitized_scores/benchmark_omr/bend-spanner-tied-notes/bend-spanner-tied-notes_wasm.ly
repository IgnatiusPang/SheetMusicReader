\version "2.26.0"
\header {
  title = "bend-spanner-tied-notes"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble a''4 a''4 a''4 b''4 \bar "|"
    a''4 a''4 a''4 b''4 \bar "|"
    a''4 a''4 a''4 b''4 \bar "|"
    c''2 d''2 \bar "|"
    \break
    d''2 d''2 \bar "|"
    c''2 c''8 d''2 \bar "|"
    d''2 d''2 \bar "|"
    c''2 r2 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
