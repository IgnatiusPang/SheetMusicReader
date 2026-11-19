\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Key Clefs"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
  ragged-last = ##f
  system-system-spacing.basic-distance = #16
}
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key cis \major \time 4/4
  % system 1
  cis'1 |  % bar 1
  \key ces \major c'1 |  % bar 2
  \key c \major c'1 |  % bar 3
  c'1 |  % bar 4
  e'1 |  % bar 5
  \break
  % system 2
  \clef soprano \key ces \major ces'1 |  % bar 6
  \key cis \major a1 |  % bar 7
  \key c \major a1 |  % bar 8
  \key ges \major aes1 |  % bar 9
  \break
  % system 3
  \clef alto \key cis \major cis'1 |  % bar 10
  \key ces \major c'1 |  % bar 11
  \key c \major c'1 |  % bar 12
  \key cis \major c'1 |  % bar 13
  \break
  % system 4
  \clef tenor \key ces \major ces'1 |  % bar 14
  \key c \major ees'1 |  % bar 15
  e'1 |  % bar 16
  \key ges \major g'1 |  % bar 17
  \break
  % system 5
  \clef alto \key b \major b'1 |  % bar 18
  \key ces \major bes'1 |  % bar 19
  \break
  % system 6
  \clef treble \key fis \major cis'1 |  % bar 20
  \key c \major c'1 |  % bar 21
  c'1 |  % bar 22
  c'1 |  % bar 23
  e'1 |  % bar 24
  \break
  % system 7
  \clef soprano \key ces \major ces'1 |  % bar 25
  \key c \major aes1 |  % bar 26
  a1 |  % bar 27
  \key ges \major aes1 |  % bar 28
  \break
  % system 8
  \clef alto \key fis \major cis'1 |  % bar 29
  \key c \major c'1 |  % bar 30
  c'1 |  % bar 31
  e'1 |  % bar 32
  e'1 |  % bar 33
  \break
  % system 9
  \clef tenor \key ges \major ces'1 |  % bar 34
  \key c \major e'1 |  % bar 35
  e'1 |  % bar 36
  \key ges \major e'1 |  % bar 37
  \break
  % system 10
  \clef bass \key fis \major cis'1 |  % bar 38
  \key ges \major ces'1 |  % bar 39
  \bar "|."
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    
  }
}
}
\score {
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key cis \major \time 4/4
  % system 1
  cis'1 |  % bar 1
  \key ces \major c'1 |  % bar 2
  \key c \major c'1 |  % bar 3
  c'1 |  % bar 4
  e'1 |  % bar 5
  \break
  % system 2
  \clef soprano \key ces \major ces'1 |  % bar 6
  \key cis \major a1 |  % bar 7
  \key c \major a1 |  % bar 8
  \key ges \major aes1 |  % bar 9
  \break
  % system 3
  \clef alto \key cis \major cis'1 |  % bar 10
  \key ces \major c'1 |  % bar 11
  \key c \major c'1 |  % bar 12
  \key cis \major c'1 |  % bar 13
  \break
  % system 4
  \clef tenor \key ces \major ces'1 |  % bar 14
  \key c \major ees'1 |  % bar 15
  e'1 |  % bar 16
  \key ges \major g'1 |  % bar 17
  \break
  % system 5
  \clef alto \key b \major b'1 |  % bar 18
  \key ces \major bes'1 |  % bar 19
  \break
  % system 6
  \clef treble \key fis \major cis'1 |  % bar 20
  \key c \major c'1 |  % bar 21
  c'1 |  % bar 22
  c'1 |  % bar 23
  e'1 |  % bar 24
  \break
  % system 7
  \clef soprano \key ces \major ces'1 |  % bar 25
  \key c \major aes1 |  % bar 26
  a1 |  % bar 27
  \key ges \major aes1 |  % bar 28
  \break
  % system 8
  \clef alto \key fis \major cis'1 |  % bar 29
  \key c \major c'1 |  % bar 30
  c'1 |  % bar 31
  e'1 |  % bar 32
  e'1 |  % bar 33
  \break
  % system 9
  \clef tenor \key ges \major ces'1 |  % bar 34
  \key c \major e'1 |  % bar 35
  e'1 |  % bar 36
  \key ges \major e'1 |  % bar 37
  \break
  % system 10
  \clef bass \key fis \major cis'1 |  % bar 38
  \key ges \major ces'1 |  % bar 39
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
