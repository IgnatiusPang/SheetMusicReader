\version "2.26.0"
\header {
  title = "clef-transposition-placement"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new StaffGroup <<
    \new Staff {
      \accidentalStyle modern
      \time 16/16 \key c \major \clef treble <c' g>1 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 16/16 \key c \major \clef treble <c' g>1 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 16/16 \key c \major \clef treble r1 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 16/16 \key c \major \clef treble r1 r2 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 16/16 \key c \major \clef bass r4*6/1 r4*6/1 r4*6/1 f4*6/1 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 16/16 \key c \major \clef bass g4*6/1 r4*6/1 r4*6/1 r4*6/1 r4*6/1 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
