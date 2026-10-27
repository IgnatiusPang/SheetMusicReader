\version "2.26.0"
\header {
  title = "beam-subdivide-compound-meter"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key f \major \clef alto f'32[ f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32 f'32] \bar "|"
    \clef treble e''32[ e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32 e''32] \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
