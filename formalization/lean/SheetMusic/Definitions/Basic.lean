/-!
# Scope Limits

This formalization models symbolic musical scores using an exact integer tick
grid (`TICKS_PER_QUARTER = 48`, `TICKS_PER_WHOLE = 192`), which represents
standard binary, dotted, double-dotted, triplet, and duplet durations as
exact natural numbers without floating-point rounding.

It covers:
1. Per-bar beat-capacity conservation under arbitrary time signatures.
2. Tick preservation under silent-rest completion and adjacent tie merging.
3. Exact tempo ratio scaling and positive-integer rhythmic augmentation.
4. Structural equivalence of sounding pitch/duration streams across formats.

It does NOT model:
1. Continuous micro-timing deviations, rubato, or acoustic audio synthesis.
2. Visual engraving geometry (staff spacing, slurs, articulation marks, lyrics).
3. Optical music recognition accuracy prior to symbolic extraction.
-/

namespace SheetMusic

/-- Exact rhythmic ticks per quarter note (crotchet). -/
def TICKS_PER_QUARTER : Nat := 48

/-- Exact rhythmic ticks per whole note (semibreve). -/
def TICKS_PER_WHOLE : Nat := 192

/-- Symbolic kind of an event within a bar. -/
inductive EventKind where
  | note
  | rest
  deriving Repr, DecidableEq, Inhabited

/-- A single symbolic event (note, chord, or rest) in integer ticks. -/
structure ScoreEvent where
  kind : EventKind
  pitches : List Nat
  ticks : Nat
  tieStart : Bool
  tieStop : Bool
  deriving Repr, DecidableEq, Inhabited

/-- A merged sounding note/chord with continuous sounding duration in ticks. -/
structure SoundingNote where
  pitches : List Nat
  ticks : Nat
  deriving Repr, DecidableEq, Inhabited

/-- One measure/bar with its time signature and symbolic event stream. -/
structure BarSpec where
  barNumber : Nat
  beats : Nat
  beatType : Nat
  expectedTicks : Nat
  events : List ScoreEvent
  deriving Repr, DecidableEq, Inhabited

/-- Complete symbolic score with rational tempo `tempoBpmNum / tempoBpmDen`. -/
structure ScoreSpec where
  title : String
  tempoBpmNum : Nat
  tempoBpmDen : Nat
  bars : List BarSpec
  deriving Repr, DecidableEq, Inhabited

/-- Total symbolic duration (notes and rests) in a sequence of events. -/
def barTicks : List ScoreEvent → Nat
  | [] => 0
  | e :: es => e.ticks + barTicks es

/-- True iff `e` is a pitched note event with strictly positive duration. -/
def isSoundingEvent (e : ScoreEvent) : Bool :=
  e.kind == .note && !e.pitches.isEmpty && e.ticks > 0

/-- Total ticks contributed by pitched note events. -/
def soundingEventTicks : List ScoreEvent → Nat
  | [] => 0
  | e :: es => (if isSoundingEvent e then e.ticks else 0) + soundingEventTicks es

/-- Total ticks of a merged sounding-note stream. -/
def soundingNoteListTicks : List SoundingNote → Nat
  | [] => 0
  | n :: ns => n.ticks + soundingNoteListTicks ns

/-- Helper extracting optional pending note ticks for induction invariants. -/
def optSoundingTicks : Option ScoreEvent → Nat
  | none => 0
  | some e => if isSoundingEvent e then e.ticks else 0

/-- Tail-structural accumulator merging consecutive tied events of matching pitches. -/
def mergeTiesAux : Option ScoreEvent → List ScoreEvent → List SoundingNote
  | none, [] => []
  | some prev, [] =>
      if isSoundingEvent prev then
        [{ pitches := prev.pitches, ticks := prev.ticks }]
      else []
  | none, e :: rest =>
      if isSoundingEvent e then
        mergeTiesAux (some e) rest
      else
        mergeTiesAux none rest
  | some prev, e :: rest =>
      if isSoundingEvent e then
        if isSoundingEvent prev && prev.tieStart && e.tieStop && prev.pitches == e.pitches then
          mergeTiesAux (some { prev with ticks := prev.ticks + e.ticks, tieStart := e.tieStart }) rest
        else
          if isSoundingEvent prev then
            { pitches := prev.pitches, ticks := prev.ticks } :: mergeTiesAux (some e) rest
          else
            mergeTiesAux (some e) rest
      else
        if isSoundingEvent prev then
          { pitches := prev.pitches, ticks := prev.ticks } :: mergeTiesAux none rest
        else
          mergeTiesAux none rest

/-- Flatten tied consecutive notes into unified sounding notes. -/
def mergeTies (es : List ScoreEvent) : List SoundingNote :=
  mergeTiesAux none es

/-- Concatenate all events across all bars in order. -/
def scoreEvents : List BarSpec → List ScoreEvent
  | [] => []
  | b :: bs => b.events ++ scoreEvents bs

/-- Sounding notes of an entire score (handles ties across barlines). -/
def soundingNotes (s : ScoreSpec) : List SoundingNote :=
  mergeTies (scoreEvents s.bars)

/-- Sum of event ticks across a list of bars. -/
def barsTotalTicks : List BarSpec → Nat
  | [] => 0
  | b :: bs => barTicks b.events + barsTotalTicks bs

/-- Sum of expected bar capacities across a list of bars. -/
def barsExpectedTicks : List BarSpec → Nat
  | [] => 0
  | b :: bs => b.expectedTicks + barsExpectedTicks bs

/-- Total symbolic ticks of a score. -/
def totalScoreTicks (s : ScoreSpec) : Nat :=
  barsTotalTicks s.bars

/-- Append a silent rest of `restTicks` ticks to the end of a bar. -/
def appendRest (b : BarSpec) (restTicks : Nat) : BarSpec :=
  { b with events := b.events ++ [{ kind := .rest, pitches := [], ticks := restTicks, tieStart := false, tieStop := false }] }

/-- Scale a score's tempo by rational factor `speedNum / speedDen`. -/
def scaleTempo (s : ScoreSpec) (speedNum speedDen : Nat) : ScoreSpec :=
  { s with
    tempoBpmNum := s.tempoBpmNum * speedNum
    tempoBpmDen := s.tempoBpmDen * speedDen }

/-- Multiply an event's tick duration by integer factor `k`. -/
def augmentEvent (k : Nat) (e : ScoreEvent) : ScoreEvent :=
  { e with ticks := k * e.ticks }

/-- Multiply all event durations in a list by integer factor `k`. -/
def augmentEvents (k : Nat) : List ScoreEvent → List ScoreEvent
  | [] => []
  | e :: es => augmentEvent k e :: augmentEvents k es

/-- Augment a bar's rhythmic values and numerator beats by integer factor `k`. -/
def augmentBar (k : Nat) (b : BarSpec) : BarSpec :=
  { b with
    beats := k * b.beats
    expectedTicks := k * b.expectedTicks
    events := augmentEvents k b.events }

/-- Augment every bar in a list by integer factor `k`. -/
def augmentBars (k : Nat) : List BarSpec → List BarSpec
  | [] => []
  | b :: bs => augmentBar k b :: augmentBars k bs

/-- Augment all symbolic durations and bar beat counts by integer factor `k`. -/
def augmentScore (k : Nat) (s : ScoreSpec) : ScoreSpec :=
  { s with bars := augmentBars k s.bars }

/-- Cross-multiplied microsecond numerator work unit (`60_000_000 / 48 = 1_250_000`). -/
def durationWorkUnits (s : ScoreSpec) : Nat :=
  1250000 * s.tempoBpmDen * totalScoreTicks s

/-- Boolean check that a single bar satisfies time-signature beat conservation. -/
def checkBarValid (b : BarSpec) : Bool :=
  b.beats > 0 &&
  b.beatType > 0 &&
  b.expectedTicks > 0 &&
  b.beatType * b.expectedTicks == b.beats * TICKS_PER_WHOLE &&
  barTicks b.events == b.expectedTicks

/-- Propositional validity contract for a single bar. -/
def BarValid (b : BarSpec) : Prop :=
  b.beats > 0 ∧
  b.beatType > 0 ∧
  b.expectedTicks > 0 ∧
  b.beatType * b.expectedTicks = b.beats * TICKS_PER_WHOLE ∧
  barTicks b.events = b.expectedTicks

/-- Boolean check that every bar in a score satisfies beat conservation. -/
def checkAllBarsValid : List BarSpec → Bool
  | [] => true
  | b :: bs => checkBarValid b && checkAllBarsValid bs

/-- Propositional validity contract for all bars in a list. -/
def AllBarsValid : List BarSpec → Prop
  | [] => True
  | b :: bs => BarValid b ∧ AllBarsValid bs

/-- Per-bar sounding-note extraction. -/
def barSummary (b : BarSpec) : List SoundingNote :=
  mergeTies b.events

/-- Propositional equivalence: both scores have valid bars and identical sounding notes. -/
def ScoreEquiv (a b : ScoreSpec) : Prop :=
  AllBarsValid a.bars ∧
  AllBarsValid b.bars ∧
  soundingNotes a = soundingNotes b

/-- Executable Boolean equivalence checker for two scores. -/
def checkScoreEquiv (a b : ScoreSpec) : Bool :=
  checkAllBarsValid a.bars &&
  checkAllBarsValid b.bars &&
  (soundingNotes a == soundingNotes b)

end SheetMusic

-- <!-- APAF Bioinformatics | Basic.lean | Approved | 2026-11-15 -->
