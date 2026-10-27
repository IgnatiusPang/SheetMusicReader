\version "2.26.0"
\header {
  title = "autochange-clefs"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new PianoStaff <<
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key c \major \clef alto r8 r4 c'8[ b8 d'8 c'8 e'8] \bar "|"
      d'8 r8 f'8[ g'8] a'2 \bar "|"
      r8 b8 r2 r8 e'8 \bar "|"
      d'8 r8 d'8[ e'8] f'2 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key c \major \clef bass g8[ b8 a8] \bar "|"
      b1 \bar "|"
      g8 r8 a8[ c'8 b8 d'8 c'8] r8 \bar "|"
      r1 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
