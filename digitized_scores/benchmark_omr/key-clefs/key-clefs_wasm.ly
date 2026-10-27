\version "2.26.0"
\header {
  title = "key-clefs"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key cis \major \clef treble cis'1 \bar "|"
    c'1 \bar "|"
    c'1 \bar "|"
    c'1 \bar "|"
    \break
    e'1 \bar "|"
    \clef alto ces'1 \bar "|"
    \clef treble a1 \bar "|"
    a1 \bar "|"
    \break
    aes1 \bar "|"
    \clef alto cis'1 \bar "|"
    \clef treble c'1 \bar "|"
    c'1 \bar "|"
    \break
    c'1 \bar "|"
    \clef tenor ces'1 \bar "|"
    \clef treble ees'1 \bar "|"
    e'1 \bar "|"
    \break
    g'1 \bar "|"
    \clef alto b'1 \bar "|"
    \clef treble bes'1 \bar "|"
    cis'1 \bar "|"
    \break
    c'1 \bar "|"
    c'1 \bar "|"
    c'1 \bar "|"
    e'1 \bar "|"
    \break
    \clef alto ces'1 \bar "|"
    \clef treble aes1 \bar "|"
    a1 \bar "|"
    aes1 \bar "|"
    \break
    \clef alto cis'1 \bar "|"
    \clef treble c'1 \bar "|"
    c'1 \bar "|"
    e'1 \bar "|"
    \break
    e'1 \bar "|"
    \clef tenor ces'1 \bar "|"
    \clef treble e'1 \bar "|"
    e'1 \bar "|"
    \break
    e'1 \bar "|"
    \clef bass cis'1 \bar "|"
    \clef treble ces'1 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
