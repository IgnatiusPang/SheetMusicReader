import SheetMusic.Definitions.Basic
import SheetMusic.Theorems.RhythmTheorems
import SheetMusic.Solutions.RhythmSolutions

/-!
# Slowdown & Augmentation Solutions

Machine-checked proofs for rational tempo slowdown (`scaleTempo`) and positive-integer
rhythmic augmentation (`augmentScore`).
-/

namespace SheetMusic

theorem scaleTempo_preserves_invariants : ScaleTempoInvarianceSpec := by
  intro s speedNum speedDen
  refine ⟨?_, ?_, ?_⟩
  · rfl
  · rfl
  · intro hBars
    exact hBars

theorem scaleTempo_duration_law : ScaleTempoDurationLawSpec := by
  intro s speedNum speedDen
  refine ⟨?_, ?_⟩
  · dsimp [durationWorkUnits, scaleTempo, totalScoreTicks]
    ac_rfl
  · dsimp [scaleTempo]
    rw [Nat.mul_assoc s.tempoBpmNum speedNum, Nat.mul_comm speedNum s.tempoBpmDen]
    ac_rfl

/-- Definitional associativity of consecutive rational tempo scalings. -/
theorem scaleTempo_compose (s : ScoreSpec) (n1 d1 n2 d2 : Nat) :
    scaleTempo (scaleTempo s n1 d1) n2 d2 = scaleTempo s (n1 * n2) (d1 * d2) := by
  simp [scaleTempo, Nat.mul_assoc]

theorem barTicks_augmentEvents (k : Nat) (es : List ScoreEvent) :
    barTicks (augmentEvents k es) = k * barTicks es := by
  induction es with
  | nil => simp [augmentEvents, barTicks]
  | cons e es ih =>
      simp [augmentEvents, augmentEvent, barTicks, ih, Nat.mul_add]

theorem augmentEvents_append (k : Nat) (xs ys : List ScoreEvent) :
    augmentEvents k (xs ++ ys) = augmentEvents k xs ++ augmentEvents k ys := by
  induction xs with
  | nil => simp [augmentEvents]
  | cons x xs ih =>
      simp [augmentEvents, ih]

theorem scoreEvents_augmentBars (k : Nat) (bs : List BarSpec) :
    scoreEvents (augmentBars k bs) = augmentEvents k (scoreEvents bs) := by
  induction bs with
  | nil => simp [augmentBars, scoreEvents, augmentEvents]
  | cons b bs ih =>
      simp [augmentBars, augmentBar, scoreEvents, augmentEvents_append, ih]

theorem isSoundingEvent_augment (k : Nat) (hk : k > 0) (e : ScoreEvent) :
    isSoundingEvent (augmentEvent k e) = isSoundingEvent e := by
  simp [isSoundingEvent, augmentEvent]
  by_cases hpos : e.ticks > 0
  · have hmul : k * e.ticks > 0 := Nat.mul_pos hk hpos
    simp [hpos, hmul]
  · have hzero : e.ticks = 0 := Nat.eq_zero_of_not_pos hpos
    simp [hzero]

theorem soundingEventTicks_augmentEvents (k : Nat) (hk : k > 0) (es : List ScoreEvent) :
    soundingEventTicks (augmentEvents k es) = k * soundingEventTicks es := by
  induction es with
  | nil => simp [augmentEvents, soundingEventTicks]
  | cons e es ih =>
      have hAug : isSoundingEvent (augmentEvent k e) = isSoundingEvent e :=
        isSoundingEvent_augment k hk e
      simp only [augmentEvents, soundingEventTicks, hAug, ih]
      by_cases hs : isSoundingEvent e = true
      · simp [hs, augmentEvent, Nat.mul_add]
      · simp [hs]

theorem augmentBar_valid (k : Nat) (hk : k > 0) (b : BarSpec) (hb : BarValid b) :
    BarValid (augmentBar k b) := by
  rcases hb with ⟨hBeats, hType, hExp, hSig, hTicks⟩
  refine ⟨Nat.mul_pos hk hBeats, hType, Nat.mul_pos hk hExp, ?_, ?_⟩
  · calc
      b.beatType * (k * b.expectedTicks)
          = k * (b.beatType * b.expectedTicks) := by ac_rfl
      _ = k * (b.beats * TICKS_PER_WHOLE) := by rw [hSig]
      _ = (k * b.beats) * TICKS_PER_WHOLE := by ac_rfl
  · simp [augmentBar, barTicks_augmentEvents, hTicks]

theorem augmentBars_valid (k : Nat) (hk : k > 0) (bs : List BarSpec) (hbs : AllBarsValid bs) :
    AllBarsValid (augmentBars k bs) := by
  induction bs with
  | nil => simp [augmentBars, AllBarsValid]
  | cons b bs ih =>
      rcases hbs with ⟨hb, hRest⟩
      exact ⟨augmentBar_valid k hk b hb, ih hRest⟩

theorem barsTotalTicks_augmentBars (k : Nat) (bs : List BarSpec) :
    barsTotalTicks (augmentBars k bs) = k * barsTotalTicks bs := by
  induction bs with
  | nil => simp [augmentBars, barsTotalTicks]
  | cons b bs ih =>
      simp [augmentBars, augmentBar, barsTotalTicks, barTicks_augmentEvents, ih, Nat.mul_add]

theorem augmentScore_preserves_laws : AugmentScoreSpec := by
  intro k s hk
  refine ⟨?_, ?_, ?_⟩
  · intro hBars
    exact augmentBars_valid k hk s.bars hBars
  · dsimp [totalScoreTicks, augmentScore]
    exact barsTotalTicks_augmentBars k s.bars
  · rw [soundingNotes_ticks_eq_events (augmentScore k s), soundingNotes_ticks_eq_events s]
    dsimp [augmentScore]
    rw [scoreEvents_augmentBars, soundingEventTicks_augmentEvents k hk]

end SheetMusic

-- <!-- APAF Bioinformatics | SlowdownSolutions.lean | Approved | 2026-11-15 -->
