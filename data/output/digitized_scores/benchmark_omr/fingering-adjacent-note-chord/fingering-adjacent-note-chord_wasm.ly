\version "2.26.0"
\header {
  title = "fingering-adjacent-note-chord"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble <e' d''>1 \bar "|"
    a'1 \bar "|"
    <e' d''>4 <fis'' a'>4 <e' d''>4 e''4 <fis'' eis'>4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
