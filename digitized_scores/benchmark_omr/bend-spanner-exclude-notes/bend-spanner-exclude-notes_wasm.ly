\version "2.26.0"
\header {
  title = "bend-spanner-exclude-notes"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new PianoStaff <<
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key c \major \clef treble <g' f'' d''>4 <g' fis'' dis''>4 <g' f'' d''>2 \bar "|"
      r4 <fis d c'>4 <fis cis' c>8 <f b, a c'>2 <f c a>2 \bar "|"
      <f'' b' a'>4 <fis'' b' ais'>4 <f'' b' a'>2 \bar "|"
      r1 \bar "|"
      \break
      << { <c'' a'>4 <e'' cis'' ais'>4 r2 } \\ { f''2 r2 } \\ { r4. <e'' c'' a'>2 r8 } >> \bar "|"
      r1 \bar "|"
      r2 <eis cis>4 <e'' c'' a'>2 \bar "|"
      <g' d'' b'>4 <e'' a'>4 <e'' cis'' a'>4 <g' d'' b'>4 \bar "|"
      \break
      <g' d'' b'>4 <e'' a'>4 <g' d'' b'>4 r4 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key c \major \clef bass r1 \bar "|"
      r2 r8 \clef bass r2 c'2 \bar "|"
      \clef treble <f d a>1 \bar "|"
      \clef bass r2 r2 \bar "|"
      \break
      r4 d'8 r2 r8 \bar "|"
      r2 r2 \bar "|"
      << { <c' d d,>2 <gis c'>4 r2 } \\ { r2 c2 } >> \bar "|"
      r1 \bar "|"
      \break
      r1 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
