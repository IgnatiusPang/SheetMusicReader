\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Cantabile"
  composer = "Charles Dancla"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
  ragged-last = ##f
  system-system-spacing.basic-distance = #16
}
\score {
\new Staff \with { midiInstrument = "violin" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4
  % system 1
  b'4.\downbow\p( c''8) d''4( g''4) |  % bar 1
  g''2 fis''2 |  % bar 2
  \set Timing.measureLength = #7/6 fis''2.( \tuplet 3/2 { g''8) a''4( } d''4*2/3) | \set Timing.measureLength = #1  % bar 3
  b''2( g''2) |  % bar 4
  d''4.( b'8) d''8( c''8 a'8 d''8) |  % bar 5
  \break
  % system 2
  d''4.( b'8) d''8( c''8 a'8 d''8) |  % bar 6
  d''4( b'4) c''4( e''4) |  % bar 7
  g'2 fis'2 |  % bar 8
  b'4.\downbow\p( c''8) d''4( g''4) |  % bar 9
  g''2 fis''2 |  % bar 10
  \break
  % system 3
  fis''4.\ff( g''8) a''4( d''4) |  % bar 11
  b''2 g''2 |  % bar 12
  a''4.\downbow\f( fis''8) a''8( g''8 e''8 a''8) |  % bar 13
  a''4.( fis''8) a''8( g''8 e''8 a''8) |  % bar 14
  \break
  % system 4
  a''8\downbow( fis''8) d''8( b'8) a'8( b'8) g'8( a'8) |  % bar 15
  fis'8( a'8) d''8( b'8) a'8( b'8) g'8( a'8) |  % bar 16
  fis'4( a'4) g'4( b'4) |  % bar 17
  d''4( fis''4) e''4( cis''4) |  % bar 18
  \break
  % system 5
  d''2\downbow cis''8( d''8 e''8 d''8) |  % bar 19
  cis''4( b''4) a''4( cis''4) |  % bar 20
  d''2\downbow cis''8( d''8 e''8 d''8) |  % bar 21
  cis''4( b''4) a''4( cis''4) |  % bar 22
  \break
  % system 6
  d''4.\downbow( cis''8) d''4.\>( cis''8) |  % bar 23
  \set Timing.measureLength = #6/5 d''4( dis''4) eis''4( e''4)\! \grace c''8( c''4*4/5) | \set Timing.measureLength = #1  % bar 24
  b'4.( c''8) d''4( g''4) |  % bar 25
  g''2 fis''2\p |  % bar 26
  fis''4.( g''8) a''4( d''4) |  % bar 27
  \break
  % system 7
  b''2 g''2 |  % bar 28
  b''4.( fis''8) a''8( g''8) d''8( b'8) |  % bar 29
  fis''4 e''4 c''4 a'4 |  % bar 30
  g'8( b'8) d''2( fis''4) |  % bar 31
  g''2\downbow\f fis''8( g''8 a''8 g''8) |  % bar 32
  \break
  % system 8
  g''2 fis''2 |  % bar 33
  c''2 b'8( c''8 d''8 c''8) |  % bar 34
  c''2 b'2 |  % bar 35
  g''2\downbow fis''8( g''8 a''8 g''8) |  % bar 36
  d''8( b'8) a'8( g'8) b'8( g'8) e'8( d'8) |  % bar 37
  \break
  % system 9
  g'8( d'8) c''8( b'8) d''8( b'8) a'8( g'8) |  % bar 38
  g'2\downbow\p fis'8( g'8 a'8 g'8) |  % bar 39
  g1( |  % bar 40
  g4) r4 r2 |  % bar 41
  \bar "|."
}
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    
  }
}
}
\score {
\new Staff \with { midiInstrument = "violin" } {
  \numericTimeSignature \clef treble \key g \major \time 4/4
  % system 1
  b'4.\downbow\p( c''8) d''4( g''4) |  % bar 1
  g''2 fis''2 |  % bar 2
  \set Timing.measureLength = #7/6 fis''2.( \tuplet 3/2 { g''8) a''4( } d''4*2/3) | \set Timing.measureLength = #1  % bar 3
  b''2( g''2) |  % bar 4
  d''4.( b'8) d''8( c''8 a'8 d''8) |  % bar 5
  \break
  % system 2
  d''4.( b'8) d''8( c''8 a'8 d''8) |  % bar 6
  d''4( b'4) c''4( e''4) |  % bar 7
  g'2 fis'2 |  % bar 8
  b'4.\downbow\p( c''8) d''4( g''4) |  % bar 9
  g''2 fis''2 |  % bar 10
  \break
  % system 3
  fis''4.\ff( g''8) a''4( d''4) |  % bar 11
  b''2 g''2 |  % bar 12
  a''4.\downbow\f( fis''8) a''8( g''8 e''8 a''8) |  % bar 13
  a''4.( fis''8) a''8( g''8 e''8 a''8) |  % bar 14
  \break
  % system 4
  a''8\downbow( fis''8) d''8( b'8) a'8( b'8) g'8( a'8) |  % bar 15
  fis'8( a'8) d''8( b'8) a'8( b'8) g'8( a'8) |  % bar 16
  fis'4( a'4) g'4( b'4) |  % bar 17
  d''4( fis''4) e''4( cis''4) |  % bar 18
  \break
  % system 5
  d''2\downbow cis''8( d''8 e''8 d''8) |  % bar 19
  cis''4( b''4) a''4( cis''4) |  % bar 20
  d''2\downbow cis''8( d''8 e''8 d''8) |  % bar 21
  cis''4( b''4) a''4( cis''4) |  % bar 22
  \break
  % system 6
  d''4.\downbow( cis''8) d''4.\>( cis''8) |  % bar 23
  \set Timing.measureLength = #6/5 d''4( dis''4) eis''4( e''4)\! \grace c''8( c''4*4/5) | \set Timing.measureLength = #1  % bar 24
  b'4.( c''8) d''4( g''4) |  % bar 25
  g''2 fis''2\p |  % bar 26
  fis''4.( g''8) a''4( d''4) |  % bar 27
  \break
  % system 7
  b''2 g''2 |  % bar 28
  b''4.( fis''8) a''8( g''8) d''8( b'8) |  % bar 29
  fis''4 e''4 c''4 a'4 |  % bar 30
  g'8( b'8) d''2( fis''4) |  % bar 31
  g''2\downbow\f fis''8( g''8 a''8 g''8) |  % bar 32
  \break
  % system 8
  g''2 fis''2 |  % bar 33
  c''2 b'8( c''8 d''8 c''8) |  % bar 34
  c''2 b'2 |  % bar 35
  g''2\downbow fis''8( g''8 a''8 g''8) |  % bar 36
  d''8( b'8) a'8( g'8) b'8( g'8) e'8( d'8) |  % bar 37
  \break
  % system 9
  g'8( d'8) c''8( b'8) d''8( b'8) a'8( g'8) |  % bar 38
  g'2\downbow\p fis'8( g'8 a'8 g'8) |  % bar 39
  g1( |  % bar 40
  g4) r4 r2 |  % bar 41
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
