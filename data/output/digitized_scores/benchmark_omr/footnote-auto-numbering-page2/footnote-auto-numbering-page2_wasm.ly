\version "2.26.0"
\header {
  title = "footnote-auto-numbering-page2"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble a1 \bar "|"
    d'4 e'4 <f' c'' a'>4 a'8[ b'8] \bar "|"
    c''8[ d''8] a'4 b'4 c''4 \bar "|"
    d'1 \bar "|"
    \break
    d''4 a'4 b'4 c''4 \bar "|"
    d''4 a'4 b'4 c''4 \bar "|"
    d''4 a'4 b'4 c''4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
