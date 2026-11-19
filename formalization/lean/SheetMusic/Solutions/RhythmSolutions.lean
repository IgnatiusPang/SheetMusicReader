import SheetMusic.Definitions.Basic
import SheetMusic.Theorems.RhythmTheorems

/-!
# Rhythm Solutions

Machine-checked proofs for bar-beat conservation, rest completion, and tie-merging
tick invariance.
-/

namespace SheetMusic

theorem whole_equals_four_quarters : WholeEqualsFourQuartersSpec := by
  rfl

theorem barTicks_append : BarTicksAppendSpec := by
  intro xs ys
  induction xs with
  | nil => simp [barTicks]
  | cons x xs ih =>
      simp [barTicks, ih]
      omega

theorem soundingEventTicks_append (xs ys : List ScoreEvent) :
    soundingEventTicks (xs ++ ys) = soundingEventTicks xs + soundingEventTicks ys := by
  induction xs with
  | nil => simp [soundingEventTicks]
  | cons x xs ih =>
      simp [soundingEventTicks, ih]
      omega

theorem appendRest_valid : RestCompletionValidSpec := by
  intro b deficit hBeats hType hExp hSig hSum
  refine ⟨hBeats, hType, hExp, hSig, ?_⟩
  dsimp [appendRest]
  rw [barTicks_append]
  simp [barTicks]
  omega

theorem checkBarValid_iff (b : BarSpec) :
    checkBarValid b = true ↔ BarValid b := by
  simp [checkBarValid, BarValid, Bool.and_eq_true]
  omega

theorem checkAllBarsValid_iff (bs : List BarSpec) :
    checkAllBarsValid bs = true ↔ AllBarsValid bs := by
  induction bs with
  | nil => simp [checkAllBarsValid, AllBarsValid]
  | cons b bs ih =>
      simp [checkAllBarsValid, AllBarsValid, checkBarValid_iff, ih]

theorem allBarsValid_totalTicks_eq_expected : AllBarsValidTotalTicksSpec := by
  intro bs hValid
  induction bs with
  | nil => simp [barsTotalTicks, barsExpectedTicks]
  | cons b bs ih =>
      rcases hValid with ⟨hb, hbs⟩
      rcases hb with ⟨_, _, _, _, hBarEq⟩
      have hRest := ih hbs
      simp [barsTotalTicks, barsExpectedTicks, hBarEq, hRest]

theorem soundingNoteListTicks_append (xs ys : List SoundingNote) :
    soundingNoteListTicks (xs ++ ys) = soundingNoteListTicks xs + soundingNoteListTicks ys := by
  induction xs with
  | nil => simp [soundingNoteListTicks]
  | cons x xs ih =>
      simp [soundingNoteListTicks, ih]
      omega

theorem mergeTiesAux_conserves_ticks (es : List ScoreEvent) :
    ∀ cur : Option ScoreEvent,
      soundingNoteListTicks (mergeTiesAux cur es) = soundingEventTicks es + optSoundingTicks cur := by
  induction es with
  | nil =>
      intro cur
      cases cur with
      | none => simp [mergeTiesAux, soundingEventTicks, optSoundingTicks, soundingNoteListTicks]
      | some prev =>
          by_cases hp : isSoundingEvent prev = true
          · simp [mergeTiesAux, hp, soundingEventTicks, optSoundingTicks, soundingNoteListTicks]
          · simp [mergeTiesAux, hp, soundingEventTicks, optSoundingTicks, soundingNoteListTicks]
  | cons e rest ih =>
      intro cur
      cases cur with
      | none =>
          by_cases he : isSoundingEvent e = true
          · have hRec := ih (some e)
            simp [mergeTiesAux, he, soundingEventTicks, optSoundingTicks] at hRec ⊢
            omega
          · have hRec := ih none
            simp [mergeTiesAux, he, soundingEventTicks, optSoundingTicks] at hRec ⊢
            omega
      | some prev =>
          by_cases he : isSoundingEvent e = true
          · by_cases hp : isSoundingEvent prev = true
            · by_cases hTie : (prev.tieStart && e.tieStop && (prev.pitches == e.pitches)) = true
              · have hMergedSound : isSoundingEvent { prev with ticks := prev.ticks + e.ticks, tieStart := e.tieStart } = true := by
                  simp [isSoundingEvent] at hp he ⊢
                  rcases hp with ⟨⟨hk, hpitch⟩, _⟩
                  rcases he with ⟨_, hepos⟩
                  exact ⟨⟨hk, hpitch⟩, Nat.add_pos_right prev.ticks hepos⟩
                have hRec := ih (some { prev with ticks := prev.ticks + e.ticks, tieStart := e.tieStart })
                simp only [mergeTiesAux, he, hp, hTie, Bool.true_and, ite_true,
                  soundingEventTicks, optSoundingTicks, hMergedSound] at hRec ⊢
                omega
              · have hRec := ih (some e)
                simp only [mergeTiesAux, he, hp, hTie, Bool.true_and, Bool.false_eq_true, ite_true, ite_false,
                  soundingEventTicks, optSoundingTicks, soundingNoteListTicks] at hRec ⊢
                omega
            · have hRec := ih (some e)
              simp only [mergeTiesAux, he, hp, Bool.false_and, Bool.false_eq_true, ite_true, ite_false,
                soundingEventTicks, optSoundingTicks] at hRec ⊢
              omega
          · by_cases hp : isSoundingEvent prev = true
            · have hRec := ih none
              simp only [mergeTiesAux, he, hp, ite_true, ite_false, Bool.false_eq_true,
                soundingEventTicks, optSoundingTicks, soundingNoteListTicks] at hRec ⊢
              omega
            · have hRec := ih none
              simp only [mergeTiesAux, he, hp, ite_false, Bool.false_eq_true,
                soundingEventTicks, optSoundingTicks] at hRec ⊢
              omega

theorem mergeTies_conserves_ticks : MergeTiesConservesTicksSpec := by
  intro es
  have h := mergeTiesAux_conserves_ticks es none
  dsimp [mergeTies]
  simp only [optSoundingTicks] at h
  exact h

theorem soundingNotes_ticks_eq_events (s : ScoreSpec) :
    soundingNoteListTicks (soundingNotes s) = soundingEventTicks (scoreEvents s.bars) := by
  exact mergeTies_conserves_ticks (scoreEvents s.bars)

end SheetMusic

-- <!-- APAF Bioinformatics | RhythmSolutions.lean | Approved | 2026-11-15 -->
