\version "2.26.0"
\header {
  title = "beam-concave-chord"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key es \major \clef treble r2 \bar "|"
    c''16[ bes'16 c''16 ees''16 g''16 <ees'' bes''>16] r4 \bar "|"
    c''16[ bes'16 c''16 ees''16 g''16 <ees'' bes''>16] r4 \bar "|"
    r2 \bar "|"
    \break
    << { c'''8[ <g'' g' c''>8 <f'' c''>8 <ees'' ees'>8 <ees'' ees'>8 <c'' c'>8 <des'' des'>8 <des'' des'>8] } \\ { <e'' c''>4 r2. } >> \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
