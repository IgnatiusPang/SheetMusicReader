\version "2.26.0"
\header {
  title = "footnote-auto-numbering-vertical-order-page1"
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
      \time 4/4 \key c \major \clef treble d'4 e'4 <f' c'' a'>4 a'8[ b'8] \bar "|"
      c''8[ d''8] a'4 b'4 c''4 \bar "|"
      d''4 a'4 b'4 c''4 \bar "|"
      d'4 e'4 <f' c'' a'>4 a'8[ b'8] \bar "|"
      \break
      c''8[ d''8] a'4 b'4 c''4 \bar "|"
      d''4 a'4 b'4 c''4 \bar "|"
      \bar "|."
    }
    \new Staff {
      \accidentalStyle modern
      \time 4/4 \key c \major \clef treble d'4 e'4 <f' c'' a'>4 a'8[ b'8] \bar "|"
      << { c''4 a'4 b'4 c''4 } \\ { r8 d''8 r2. } >> \bar "|"
      d''4 a'4 b'4 c''4 \bar "|"
      d'4 e'4 <f' c'' a'>4 a'8[ b'8] \bar "|"
      \break
      << { c''4 a'4 b'4 c''4 } \\ { r8 d''8 r2. } >> \bar "|"
      d''4 a'4 b'4 c''4 \bar "|"
      \bar "|."
    }
  >>
  \layout { }
  \midi { }
}
