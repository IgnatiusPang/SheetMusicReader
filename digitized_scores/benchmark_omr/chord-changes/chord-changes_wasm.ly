\version "2.26.0"
\header {
  title = "chord-changes"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 2/4 \key f \major \clef treble r2 \bar "|"
    r2 \bar "|"
    <g'' ees'' c''>1 \bar "|"
    r2 \bar "|"
    \break
    r2 \bar "|"
    r2 \bar "|"
    r2 \bar "|"
    <g'' ees'' c''>1 \bar "|"
    \break
    r2 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
