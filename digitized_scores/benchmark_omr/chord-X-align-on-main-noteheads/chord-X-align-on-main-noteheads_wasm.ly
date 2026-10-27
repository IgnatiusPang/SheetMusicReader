\version "2.26.0"
\header {
  title = "chord-X-align-on-main-noteheads"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble e''4 e''4 <e'' c''>4 <e'' d'' a'>4 \bar "|"
    f''4 e''4 f''4 f''4 \bar "|"
    f'4 f'4 <f' a'>4 <f' c''>8 r8 \bar "|"
    e'4 f'4 e'4 e'4 \bar "|"
    \break
    \bar "|."
  }
  \layout { }
  \midi { }
}
