import SheetMusic.Definitions.Basic
import SheetMusic.Theorems.RhythmTheorems
import SheetMusic.Solutions.RhythmSolutions
import SheetMusic.Solutions.SlowdownSolutions
import SheetMusic.Solutions.TranslationSolutions

/-!
# SheetMusic Axiom Audit & Compilation Smoke Runner
-/

open SheetMusic

#check whole_equals_four_quarters
#check barTicks_append
#check soundingEventTicks_append
#check appendRest_valid
#check checkBarValid_iff
#check checkAllBarsValid_iff
#check allBarsValid_totalTicks_eq_expected
#check soundingNoteListTicks_append
#check mergeTiesAux_conserves_ticks
#check mergeTies_conserves_ticks
#check soundingNotes_ticks_eq_events
#check scaleTempo_preserves_invariants
#check scaleTempo_duration_law
#check scaleTempo_compose
#check barTicks_augmentEvents
#check augmentEvents_append
#check scoreEvents_augmentBars
#check isSoundingEvent_augment
#check soundingEventTicks_augmentEvents
#check augmentBar_valid
#check augmentBars_valid
#check barsTotalTicks_augmentBars
#check augmentScore_preserves_laws
#check checkScoreEquiv_iff
#check scoreEquiv_refl
#check scoreEquiv_symm
#check scoreEquiv_trans
#check scoreEquiv_sounding_ticks

#print axioms whole_equals_four_quarters
#print axioms barTicks_append
#print axioms soundingEventTicks_append
#print axioms appendRest_valid
#print axioms checkBarValid_iff
#print axioms checkAllBarsValid_iff
#print axioms allBarsValid_totalTicks_eq_expected
#print axioms soundingNoteListTicks_append
#print axioms mergeTiesAux_conserves_ticks
#print axioms mergeTies_conserves_ticks
#print axioms soundingNotes_ticks_eq_events
#print axioms scaleTempo_preserves_invariants
#print axioms scaleTempo_duration_law
#print axioms scaleTempo_compose
#print axioms barTicks_augmentEvents
#print axioms augmentEvents_append
#print axioms scoreEvents_augmentBars
#print axioms isSoundingEvent_augment
#print axioms soundingEventTicks_augmentEvents
#print axioms augmentBar_valid
#print axioms augmentBars_valid
#print axioms barsTotalTicks_augmentBars
#print axioms augmentScore_preserves_laws
#print axioms checkScoreEquiv_iff
#print axioms scoreEquiv_refl
#print axioms scoreEquiv_symm
#print axioms scoreEquiv_trans
#print axioms scoreEquiv_sounding_ticks

def main : IO Unit := pure ()

-- <!-- APAF Bioinformatics | TestRunner.lean | Approved | 2026-11-15 -->
