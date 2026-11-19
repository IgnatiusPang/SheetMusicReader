\version "2.26.0"
\header {
  title = "chord-repetition-times"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble <g' e' c'>4 r4 <g' d' b>2 \bar "|"
    << { <g' d' c'>4*4/5 g'4*4/11[ g'4*4/11 d'4*1/7 g'4*1/7] r2 r32 } \\ { r8. <d' c'>4*4/5 <d' c'>4*2/11 r2 r32 } \\ { r4 r32 <d' c'>4*4/5 r2 } \\ { r4. g'4*4/11 r2 } >> \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
