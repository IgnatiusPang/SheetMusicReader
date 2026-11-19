\version "2.26.0"
\header {
  title = "chord-dots"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key c \major \clef treble << { <f' d'' a'>16. r16 r16. <e'' c'' a'>64 r8. r16 } \\ { r4 <g'' f' c'>4*3/16 r8. } >> \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
