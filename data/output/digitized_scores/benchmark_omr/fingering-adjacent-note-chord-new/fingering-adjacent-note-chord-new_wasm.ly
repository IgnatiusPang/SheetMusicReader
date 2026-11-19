\version "2.26.0"
\header {
  title = "fingering-adjacent-note-chord-new"
  tagline = ##f
}
\paper {
  #(set-paper-size "a4")
  indent = 0
}
\score {
  \new Staff {
    \accidentalStyle modern
    \time 4/4 \key c \major \clef treble <c' e'>1 \bar "|"
    <d'' b' a''>1 \bar "|"
    <e'' e' d''>4 <fis'' b' a'>4 <e'' e' d''>4 <fis'' e'' eis'>4 \bar "|"
    <e' d'' b'>1 \bar "|"
    \break
    <e'' e' d''>4 <fis'' b' a'>4 <e'' e' d''>4 <fis'' e'' eis'>4 \bar "|"
    \bar "|."
  }
  \layout { }
  \midi { }
}
