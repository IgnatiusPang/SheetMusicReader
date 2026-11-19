\version "2.26.0"
\header {
  title = "cue-clef-keysignature"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key g \major \clef treble g'4 g'4 g'4 g'4 \bar "|"
    \clef bass c1 \bar "|"
    \clef alto g'4 g'4 g'4 g'4 \bar "|"
    \clef bass d4 d4 d4 d4 \bar "|"
    \break
    \clef treble c1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
