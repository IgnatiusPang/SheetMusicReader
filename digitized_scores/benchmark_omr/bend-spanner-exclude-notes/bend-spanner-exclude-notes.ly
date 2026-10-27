\version "2.24.0"
% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->
\header {
  title = "Bend Spanner Exclude Notes"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
  ragged-last = ##f
  system-system-spacing.basic-distance = #16
}
\score {
\new PianoStaff <<
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  <g' f'' d''>4 <g' fis'' dis''>4 <g' f'' d''>2 |  % bar 1
  \set Timing.measureLength = #13/8 r4 <fis d c'>4 <fis cis' c>8 <f b, a c'>2 <f c a>2 | \set Timing.measureLength = #1  % bar 2
  <f'' b' a'>4 <fis'' b' ais'>4 <f'' b' a'>2\fermata |  % bar 3
  r1 |  % bar 4
  <c'' a'>4 <e'' cis'' ais'>4 r2 |  % bar 5
  r1 |  % bar 6
  \set Timing.measureLength = #5/4 r2 <eis cis>4 <e'' c'' a'>2 | \set Timing.measureLength = #1  % bar 7
  \break
  % system 2
  <g' d'' b'>4 <e'' a'>4 <e'' cis'' a'>4 <g' d'' b'>4 |  % bar 8
  <g' d'' b'>4 <e'' a'>4 <g' d'' b'>4 r4 |  % bar 9
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef bass \key c \major \time 4/4
  % system 1
  r1 |  % bar 1
  \clef tenor \set Timing.measureLength = #13/8 r2 r8 \clef bass r2 c'2->\fermata | \set Timing.measureLength = #1  % bar 2
  \clef treble <f d a>1 |  % bar 3
  r2 r2 |  % bar 4
  r2 r2 |  % bar 5
  r2 r2 |  % bar 6
  \set Timing.measureLength = #5/4 <c' d d,>2 <gis c'>4 r2 | \set Timing.measureLength = #1  % bar 7
  \break
  % system 2
  r1 |  % bar 8
  r1 |  % bar 9
  \bar "|."
}
>>
\layout {
  \context { \Score
    \override NonMusicalPaperColumn.line-break-permission = ##f
    
  }
}
}
\score {
\new PianoStaff <<
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef treble \key c \major \time 4/4
  % system 1
  <g' f'' d''>4 <g' fis'' dis''>4 <g' f'' d''>2 |  % bar 1
  \set Timing.measureLength = #13/8 r4 <fis d c'>4 <fis cis' c>8 <f b, a c'>2 <f c a>2 | \set Timing.measureLength = #1  % bar 2
  <f'' b' a'>4 <fis'' b' ais'>4 <f'' b' a'>2\fermata |  % bar 3
  r1 |  % bar 4
  <c'' a'>4 <e'' cis'' ais'>4 r2 |  % bar 5
  r1 |  % bar 6
  \set Timing.measureLength = #5/4 r2 <eis cis>4 <e'' c'' a'>2 | \set Timing.measureLength = #1  % bar 7
  \break
  % system 2
  <g' d'' b'>4 <e'' a'>4 <e'' cis'' a'>4 <g' d'' b'>4 |  % bar 8
  <g' d'' b'>4 <e'' a'>4 <g' d'' b'>4 r4 |  % bar 9
  \bar "|."
}
\new Staff \with { midiInstrument = "acoustic grand" } {
  \numericTimeSignature \clef bass \key c \major \time 4/4
  % system 1
  r1 |  % bar 1
  \clef tenor \set Timing.measureLength = #13/8 r2 r8 \clef bass r2 c'2->\fermata | \set Timing.measureLength = #1  % bar 2
  \clef treble <f d a>1 |  % bar 3
  r2 r2 |  % bar 4
  r2 r2 |  % bar 5
  r2 r2 |  % bar 6
  \set Timing.measureLength = #5/4 <c' d d,>2 <gis c'>4 r2 | \set Timing.measureLength = #1  % bar 7
  \break
  % system 2
  r1 |  % bar 8
  r1 |  % bar 9
  \bar "|."
}
>>
\midi { \tempo 4 = 90 }
}
