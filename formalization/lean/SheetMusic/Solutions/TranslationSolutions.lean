import SheetMusic.Definitions.Basic
import SheetMusic.Theorems.RhythmTheorems
import SheetMusic.Solutions.RhythmSolutions

/-!
# Translation Equivalence Solutions

Machine-checked proofs of soundness/completeness of `checkScoreEquiv`, plus
reflexivity, symmetry, transitivity, and sounding-tick conservation across
translations (original ↔ MusicXML ↔ LilyPond ↔ MIDI).
-/

namespace SheetMusic

theorem checkScoreEquiv_iff : CheckScoreEquivSoundSpec := by
  intro a b
  simp [checkScoreEquiv, ScoreEquiv, Bool.and_eq_true, checkAllBarsValid_iff, and_assoc]

theorem scoreEquiv_refl :
    ∀ a : ScoreSpec, AllBarsValid a.bars → ScoreEquiv a a := by
  intro a hValid
  exact ⟨hValid, hValid, rfl⟩

theorem scoreEquiv_symm :
    ∀ a b : ScoreSpec, ScoreEquiv a b → ScoreEquiv b a := by
  intro a b hab
  exact ⟨hab.2.1, hab.1, hab.2.2.symm⟩

theorem scoreEquiv_trans : ScoreEquivTransSpec := by
  intro a b c hab hbc
  exact ⟨hab.1, hbc.2.1, hab.2.2.trans hbc.2.2⟩

theorem scoreEquiv_sounding_ticks :
    ∀ a b : ScoreSpec, ScoreEquiv a b →
      soundingNoteListTicks (soundingNotes a) = soundingNoteListTicks (soundingNotes b) := by
  intro a b hab
  rw [hab.2.2]

end SheetMusic

-- <!-- APAF Bioinformatics | TranslationSolutions.lean | Approved | 2026-11-15 -->
