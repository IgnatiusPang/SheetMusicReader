\version "2.26.0"
\header {
  title = "beam-rest-extreme"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble <f''' f'' c'''>16 r16 <f''' f'' c''' bes''>16[ <f''' f'' c''' bes''>16 <f''' f'' c''' bes''>16] r16 f'''16[ f'''16 d'''16 d'''16] r16 <f''' f'' c''' bes''>16[ <f''' f'' c''' bes''>16 <f'' f' c'' bes'>16] r16 <f'' f' c'' bes'>16[ <f'' f' c'' bes'>16] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
