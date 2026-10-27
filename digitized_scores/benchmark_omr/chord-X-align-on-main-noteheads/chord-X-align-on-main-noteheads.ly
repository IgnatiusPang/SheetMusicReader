\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Chord X Align On Main Noteheads"
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
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  e''4-> e''4-> <e'' c''>4-> <e'' d'' a'>4-> |  % bar 1
  f''4( e''4) f''4( f''4) |  % bar 2
  f'4 f'4 <f' a'>4 <f' c''>8 r8 |  % bar 3
  e'4( f'4) e'4( e'4) |  % bar 4
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
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  e''4-> e''4-> <e'' c''>4-> <e'' d'' a'>4-> |  % bar 1
  f''4( e''4) f''4( f''4) |  % bar 2
  f'4 f'4 <f' a'>4 <f' c''>8 r8 |  % bar 3
  e'4( f'4) e'4( e'4) |  % bar 4
  \bar "|."
}
\midi { \tempo 4 = 90 }
}
