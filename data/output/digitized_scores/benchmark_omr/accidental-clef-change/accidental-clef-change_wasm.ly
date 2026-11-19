\version "2.26.0"
\header {
  title = "accidental-clef-change"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key g \major \clef treble cis'4 dis'4 f'4 \clef bass <fis' cis'>4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
