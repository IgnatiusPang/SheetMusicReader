import SheetMusic.Definitions.Basic

/-!
# Rhythm & Translation Theorem Contracts

Formal propositional specifications proven in `SheetMusic.Solutions.*`.
-/

namespace SheetMusic

/-- Contract: `TICKS_PER_WHOLE` is four quarter notes. -/
def WholeEqualsFourQuartersSpec : Prop :=
  TICKS_PER_WHOLE = 4 * TICKS_PER_QUARTER

/-- Contract: total bar ticks add across list concatenation. -/
def BarTicksAppendSpec : Prop :=
  ∀ xs ys : List ScoreEvent, barTicks (xs ++ ys) = barTicks xs + barTicks ys

/-- Contract: appending the exact missing deficit rest makes an under-filled bar valid. -/
def RestCompletionValidSpec : Prop :=
  ∀ (b : BarSpec) (deficit : Nat),
    b.beats > 0 →
    b.beatType > 0 →
    b.expectedTicks > 0 →
    b.beatType * b.expectedTicks = b.beats * TICKS_PER_WHOLE →
    barTicks b.events + deficit = b.expectedTicks →
    BarValid (appendRest b deficit)

/-- Contract: tie merging conserves total sounding note duration. -/
def MergeTiesConservesTicksSpec : Prop :=
  ∀ es : List ScoreEvent, soundingNoteListTicks (mergeTies es) = soundingEventTicks es

/-- Contract: score-wide bar validity implies total ticks equal total bar capacities. -/
def AllBarsValidTotalTicksSpec : Prop :=
  ∀ bs : List BarSpec, AllBarsValid bs → barsTotalTicks bs = barsExpectedTicks bs

/-- Contract: tempo scaling leaves bar structure and sounding notes invariant. -/
def ScaleTempoInvarianceSpec : Prop :=
  ∀ (s : ScoreSpec) (speedNum speedDen : Nat),
    totalScoreTicks (scaleTempo s speedNum speedDen) = totalScoreTicks s ∧
    soundingNotes (scaleTempo s speedNum speedDen) = soundingNotes s ∧
    (AllBarsValid s.bars → AllBarsValid (scaleTempo s speedNum speedDen).bars)

/-- Contract: tempo scaling scales duration work units linearly by `speedDen`. -/
def ScaleTempoDurationLawSpec : Prop :=
  ∀ (s : ScoreSpec) (speedNum speedDen : Nat),
    durationWorkUnits (scaleTempo s speedNum speedDen) = speedDen * durationWorkUnits s ∧
    (scaleTempo s speedNum speedDen).tempoBpmNum * s.tempoBpmDen * speedDen =
      s.tempoBpmNum * (scaleTempo s speedNum speedDen).tempoBpmDen * speedNum

/-- Contract: positive-integer rhythmic augmentation preserves bar validity and scales ticks by `k`. -/
def AugmentScoreSpec : Prop :=
  ∀ (k : Nat) (s : ScoreSpec),
    k > 0 →
    (AllBarsValid s.bars → AllBarsValid (augmentScore k s).bars) ∧
    totalScoreTicks (augmentScore k s) = k * totalScoreTicks s ∧
    soundingNoteListTicks (soundingNotes (augmentScore k s)) = k * soundingNoteListTicks (soundingNotes s)

/-- Contract: `checkScoreEquiv` reflects `ScoreEquiv` soundness and completeness. -/
def CheckScoreEquivSoundSpec : Prop :=
  ∀ a b : ScoreSpec, checkScoreEquiv a b = true ↔ ScoreEquiv a b

/-- Contract: `ScoreEquiv` is transitive across multi-stage format translations. -/
def ScoreEquivTransSpec : Prop :=
  ∀ a b c : ScoreSpec, ScoreEquiv a b → ScoreEquiv b c → ScoreEquiv a c

end SheetMusic

-- <!-- APAF Bioinformatics | RhythmTheorems.lean | Approved | 2026-11-15 -->
