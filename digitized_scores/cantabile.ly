\version "2.26.0"
% Cantabile - Charles Dancla (1817-1907), edited Samuel Applebaum (AMEB Violin Series, List A No 1)
% Transcribed from data/cantabile.jpeg; every notehead verified against an OMR point cloud of the photo.
% <!-- APAF Bioinformatics | cantabile.ly | Approved | 2026-10-22 -->

\header {
  title = "Cantabile"
  poet = \markup \bold "LIST A No 1"
  composer = \markup \right-column {
    \line { "Charles Dancla" }
    \line { "(1817 – 1907)" }
    \line { \italic "edited Samuel Applebaum" }
  }
  tagline = ##f
}

\paper {
  #(set-paper-size "a4")
  indent = 0
  ragged-bottom = ##f
  ragged-last-bottom = ##f
  top-margin = 14\mm
  bottom-margin = 14\mm
  left-margin = 14\mm
  right-margin = 14\mm
  system-system-spacing.basic-distance = #18
}

crescText = ^\markup \italic "cresc."
crescBelow = _\markup \italic "cresc."
dimBelow = _\markup \italic "dim."
ritenAbove = ^\markup \italic "riten."
ritardAbove = ^\markup \italic "ritard."
aTempoAbove = ^\markup \bold "a tempo"

violin = \relative c'' {
  \clef treble
  \key g \major
  \numericTimeSignature
  \time 4/4
  \tempo "Andante" 4 = 80-96
  \override Score.BarNumber.font-shape = #'italic

  % ---- System 1: m1-5
  b4.^\downbow^1\p( c8\<) d4( g4) |                                 % 1
  g2\> fis2\! |                                                     % 2
  fis4.^\downbow^1( g8) a4^3( d,4) |                                % 3
  b'2^4 g2 |                                                        % 4
  d4.^\downbow^3( b8) d8[( c a^0 d^3)] |                            % 5
  \break
  % ---- System 2: m6-10
  d4.( b8) d8[( c a^0 d^3)] |                                       % 6
  d4^\downbow( b4) c4( e4^4) |                                      % 7
  g,2^3\> fis2\! |                                                  % 8
  b4.^\downbow^1\p( c8\<) d4( g4) |                                 % 9
  g2\> fis2\! |                                                     % 10
  \break
  % ---- System 3: m11-14
  fis4.^\downbow\crescBelow( g8) a4^3( d,4) |                       % 11
  b'2^4 g2 |                                                        % 12
  a4.^\downbow\f( fis8) a8[( g e^0 a)] |                            % 13
  a4.( fis8) a8[( g e^0 a)] |                                       % 14
  \break
  % ---- System 4: m15-18
  a8^\downbow[( fis) d^3( b)] a^0[( b) g( a^4)] |                   % 15
  fis8[( a^0) d( b)] a[( b) g( a^4)] |                              % 16
  fis4^\downbow( a4^4) g4( b4) |                                    % 17
  d4( fis4) e4^4( cis4) |                                           % 18
  \break
  % ---- System 5: m19-22
  d2^\downbow cis8^2[( d e^4 d)] |                                  % 19
  cis4^2( b'4^4) a4( cis,4) |                                       % 20
  d2^\downbow cis8^2[( d e^4 d)] |                                  % 21
  cis4^2( b'4^4) a4( cis,4) |                                       % 22
  \break
  % ---- System 6: m23-27
  d4.^\downbow( cis8) d4.\ritenAbove\>( cis8) |                     % 23
  d4( dis4^3) e4^4( c?4^2\!) |                                      % 24
  b4.^\downbow^1\aTempoAbove\p( c8) d?4( g4) |                      % 25
  g2 fis2 |                                                         % 26
  fis4.^\downbow^1( g8) a4^3( d,4) |                                % 27
  \break
  % ---- System 7: m28-32
  b'2^4 g2 |                                                        % 28
  b4.^\downbow( fis8) a8[( g) d( b)] |                              % 29
  fis'4\crescBelow e4^0 c4 a4 |                                     % 30
  g8[( b)] d2^3( fis4) |                                            % 31
  g2^\downbow\f fis8[( g a g)] |                                    % 32
  \break
  % ---- System 8: m33-37
  g2 fis2 |                                                         % 33
  c2^\downbow b8[( c d c)] |                                        % 34
  c2 b2 |                                                           % 35
  g'2^\downbow^2\f fis8[( g a g)] |                                 % 36
  d8^3\dimBelow[( b) a( g)] b^4[( g) e( d)] |                       % 37
  \break
  % ---- System 9: m38-41
  g8^\downbow[( d) c'^2( b)] d[( b) a^4( g^3)] |                    % 38
  g2^\downbow\ritardAbove\p fis8^2[( g a^4 g)] |                    % 39
  g,1~ |                                                            % 40
  g4 r4 r2 \bar "|."                                                % 41
}

\score {
  \new Staff \violin
  \layout { }
  \midi { \tempo 4 = 88 }
}
