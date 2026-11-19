\version "2.26.0"
\header {
  title = "accidental-contemporary"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble gis'4 a'4 gis'4 g'4 \bar "|"
    gis'8[ a'8 gis'8 gis'8 g''8 gis''8 gis8 a'8] \bar "|"
    eis'8[ fis'8 eis'8 eis'8] gis'2 \bar "|"
    r4 r2. \bar "|"
    \break
    e'8[ eis'8 fis'8 fis'8] gis'2 \bar "|"
    gis'4 a'4 gis'4 g'4 \bar "|"
    gis'8[ a'8 gis'8 gis'8 g''8 gis''8 gis8 a'8] \bar "|"
    eis'8[ fis'8 eis'8 eis'8] g'2 \bar "|"
    \break
    r4 e'8[ eis'8 fis'8 fis'8] gis'2 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
