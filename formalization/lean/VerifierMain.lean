import SheetMusic.Definitions.Basic
import SheetMusic.Theorems.RhythmTheorems
import SheetMusic.Solutions.RhythmSolutions
import SheetMusic.Solutions.SlowdownSolutions
import SheetMusic.Solutions.TranslationSolutions

/-!
# Concrete Score Bundle Kernel Verifier (`score_verifier`)

Reads a pipe-delimited symbolic score bundle generated from parsed original,
MusicXML, LilyPond, MIDI, and slowed editions, verifies bar-beat conservation
and cross-format sounding equivalence using compiled Lean 4 evaluators, and
emits a structured JSON audit report.
-/

open SheetMusic

structure ScoreBundleEntry where
  name : String
  augFactor : Nat
  speedNum : Nat
  speedDen : Nat
  score : ScoreSpec
  deriving Repr

structure NotesBundleEntry where
  name : String
  augFactor : Nat
  speedNum : Nat
  speedDen : Nat
  tempoNum : Nat
  tempoDen : Nat
  notes : List SoundingNote
  deriving Repr

structure RepStatus where
  name : String
  kind : String
  bars : Nat
  barsValid : Bool
  soundingNotesCount : Nat
  equivToRef : Bool
  tempoOk : Bool
  augFactor : Nat
  deriving Repr

private def jsonEscape (s : String) : String :=
  s.foldl
    (fun acc c =>
      match c with
      | '\\' => acc ++ "\\\\"
      | '"' => acc ++ "\\\""
      | '\n' => acc ++ "\\n"
      | '\r' => acc ++ "\\r"
      | '\t' => acc ++ "\\t"
      | _ => acc.push c)
    ""

private def trimStr (s : String) : String :=
  s.trimAscii.toString

private def parseNatOr (s : String) (default : Nat) : Nat :=
  match (trimStr s).toNat? with
  | some n => n
  | none => default

private def parsePitches (s : String) : List Nat :=
  let trimmed := trimStr s
  if trimmed.isEmpty then []
  else
    (trimmed.splitOn ",").filterMap fun tok =>
      let t := trimStr tok
      if t.isEmpty then none else t.toNat?

inductive BundleItem where
  | score (entry : ScoreBundleEntry)
  | notes (entry : NotesBundleEntry)

structure ParseState where
  items : List BundleItem := []
  curScore : Option (ScoreBundleEntry × Option BarSpec) := none
  curNotes : Option NotesBundleEntry := none

private def flushBar (st : ParseState) : ParseState :=
  match st.curScore with
  | some (entry, some bar) =>
      let updatedEntry := { entry with score := { entry.score with bars := entry.score.bars ++ [bar] } }
      { st with curScore := some (updatedEntry, none) }
  | _ => st

private def flushCurrent (st : ParseState) : ParseState :=
  let st1 := flushBar st
  let st2 :=
    match st1.curScore with
    | some (entry, _) => { st1 with items := st1.items ++ [BundleItem.score entry], curScore := none }
    | none => st1
  match st2.curNotes with
  | some entry => { st2 with items := st2.items ++ [BundleItem.notes entry], curNotes := none }
  | none => st2

private def parseLine (st : ParseState) (rawLine : String) : ParseState :=
  let line := trimStr rawLine
  if line.isEmpty || line.startsWith "#" then st
  else
    let cols := line.splitOn "|"
    match cols with
    | "SCORE" :: name :: tNum :: tDen :: aug :: sNum :: sDen :: _ =>
        let st' := flushCurrent st
        let entry : ScoreBundleEntry := {
          name := name
          augFactor := parseNatOr aug 1
          speedNum := parseNatOr sNum 1
          speedDen := parseNatOr sDen 1
          score := {
            title := name
            tempoBpmNum := parseNatOr tNum 100
            tempoBpmDen := parseNatOr tDen 1
            bars := []
          }
        }
        { st' with curScore := some (entry, none) }
    | "BAR" :: barNum :: beats :: beatType :: expTicks :: _ =>
        let st' := flushBar st
        match st'.curScore with
        | some (entry, _) =>
            let bar : BarSpec := {
              barNumber := parseNatOr barNum 1
              beats := parseNatOr beats 4
              beatType := parseNatOr beatType 4
              expectedTicks := parseNatOr expTicks 192
              events := []
            }
            { st' with curScore := some (entry, some bar) }
        | none => st'
    | "EV" :: kindStr :: ticksStr :: tsStr :: tstopStr :: pitchesStr :: _ =>
        match st.curScore with
        | some (entry, some bar) =>
            let ev : ScoreEvent := {
              kind := if kindStr == "R" then .rest else .note
              pitches := parsePitches pitchesStr
              ticks := parseNatOr ticksStr 0
              tieStart := tsStr == "1"
              tieStop := tstopStr == "1"
            }
            let bar' := { bar with events := bar.events ++ [ev] }
            { st with curScore := some (entry, some bar') }
        | _ => st
    | "NOTES" :: name :: aug :: sNum :: sDen :: tNum :: tDen :: _ =>
        let st' := flushCurrent st
        let entry : NotesBundleEntry := {
          name := name
          augFactor := parseNatOr aug 1
          speedNum := parseNatOr sNum 1
          speedDen := parseNatOr sDen 1
          tempoNum := parseNatOr tNum 0
          tempoDen := parseNatOr tDen 1
          notes := []
        }
        { st' with curNotes := some entry }
    | "SN" :: ticksStr :: pitchesStr :: _ =>
        match st.curNotes with
        | some entry =>
            let sn : SoundingNote := {
              pitches := parsePitches pitchesStr
              ticks := parseNatOr ticksStr 0
            }
            { st with curNotes := some { entry with notes := entry.notes ++ [sn] } }
        | none => st
    | _ => st

private def parseBundle (text : String) : List BundleItem :=
  let finalSt := (text.splitOn "\n").foldl parseLine {}
  (flushCurrent finalSt).items

private def collectBarFailures (scoreName : String) : List BarSpec → List String
  | [] => []
  | b :: bs =>
      let rest := collectBarFailures scoreName bs
      if checkBarValid b then rest
      else
        let sigOk := b.beats > 0 && b.beatType > 0 && b.expectedTicks > 0 && b.beatType * b.expectedTicks == b.beats * TICKS_PER_WHOLE
        let actual := barTicks b.events
        let msg :=
          if !sigOk then
            s!"{scoreName} bar {b.barNumber}: time signature {b.beats}/{b.beatType} disagrees with expected {b.expectedTicks} ticks"
          else
            s!"{scoreName} bar {b.barNumber}: got {actual} ticks, expected {b.expectedTicks} ticks"
        msg :: rest

private def firstNoteMismatchAux (idx : Nat) : List SoundingNote → List SoundingNote → Option String
  | [], [] => none
  | a :: as, b :: bs =>
      if a == b then firstNoteMismatchAux (idx + 1) as bs
      else some s!"note index {idx} mismatch (expected ticks={a.ticks} pitches={a.pitches}, got ticks={b.ticks} pitches={b.pitches})"
  | _ :: _, [] => some s!"note stream truncated at index {idx}"
  | [], _ :: _ => some s!"extra trailing note at index {idx}"

private def expectedRefScore (ref : ScoreSpec) (aug : Nat) : ScoreSpec :=
  if aug > 1 then augmentScore aug ref else ref

private def boolJson (b : Bool) : String :=
  if b then "true" else "false"

private def repToJson (r : RepStatus) : String :=
  "{" ++
    s!"\"name\":\"{jsonEscape r.name}\"," ++
    s!"\"kind\":\"{jsonEscape r.kind}\"," ++
    s!"\"bars\":{r.bars}," ++
    s!"\"bars_valid\":{boolJson r.barsValid}," ++
    s!"\"sounding_notes\":{r.soundingNotesCount}," ++
    s!"\"equiv_to_ref\":{boolJson r.equivToRef}," ++
    s!"\"tempo_ok\":{boolJson r.tempoOk}," ++
    s!"\"aug_factor\":{r.augFactor}" ++
  "}"

private def verifyBundle (items : List BundleItem) : Bool × String :=
  match items with
  | [] =>
      let json := "{\"ok\":false,\"all_bars_valid\":false,\"reference\":\"\",\"checked_bars\":0,\"sounding_notes\":0,\"total_ticks\":0,\"representations\":[],\"failures\":[\"Empty score bundle\"]}"
      (false, json)
  | .notes _ :: _ =>
      let json := "{\"ok\":false,\"all_bars_valid\":false,\"reference\":\"\",\"checked_bars\":0,\"sounding_notes\":0,\"total_ticks\":0,\"representations\":[],\"failures\":[\"First bundle entry must be a reference SCORE\"]}"
      (false, json)
  | .score refEntry :: _ =>
      let ref := refEntry.score
      let refBarsOk := checkAllBarsValid ref.bars
      let refSounding := soundingNotes ref
      let evalResults := items.map fun item =>
        match item with
        | .score entry =>
            let barsOk := checkAllBarsValid entry.score.bars
            let barFails := collectBarFailures entry.name entry.score.bars
            let targetRef := expectedRefScore ref entry.augFactor
            let targetSounding := soundingNotes targetRef
            let curSounding := soundingNotes entry.score
            let equiv := barsOk && refBarsOk && (curSounding == targetSounding)
            let equivFails :=
              match firstNoteMismatchAux 0 targetSounding curSounding with
              | some m => [s!"{entry.name} vs {refEntry.name}: {m}"]
              | none => []
            let tempoOk :=
              entry.speedNum > 0 && entry.speedDen > 0 && entry.score.tempoBpmNum > 0 && entry.score.tempoBpmDen > 0 &&
              entry.score.tempoBpmNum * ref.tempoBpmDen * entry.speedDen ==
                ref.tempoBpmNum * entry.score.tempoBpmDen * entry.speedNum
            let tempoFails :=
              if tempoOk then []
              else [s!"{entry.name}: tempo {entry.score.tempoBpmNum}/{entry.score.tempoBpmDen} disagrees with reference {ref.tempoBpmNum}/{ref.tempoBpmDen} * {entry.speedNum}/{entry.speedDen}"]
            let rep : RepStatus := {
              name := entry.name
              kind := "score"
              bars := entry.score.bars.length
              barsValid := barsOk
              soundingNotesCount := curSounding.length
              equivToRef := equiv
              tempoOk := tempoOk
              augFactor := entry.augFactor
            }
            (rep, barFails ++ equivFails ++ tempoFails)
        | .notes entry =>
            let targetRef := expectedRefScore ref entry.augFactor
            let targetSounding := soundingNotes targetRef
            let equiv := refBarsOk && (entry.notes == targetSounding)
            let equivFails :=
              match firstNoteMismatchAux 0 targetSounding entry.notes with
              | some m => [s!"{entry.name} vs {refEntry.name}: {m}"]
              | none => []
            let tempoOk :=
              if entry.tempoNum == 0 then true
              else
                entry.speedNum > 0 && entry.speedDen > 0 && entry.tempoDen > 0 &&
                entry.tempoNum * ref.tempoBpmDen * entry.speedDen ==
                  ref.tempoBpmNum * entry.tempoDen * entry.speedNum
            let tempoFails :=
              if tempoOk then []
              else [s!"{entry.name}: MIDI tempo {entry.tempoNum}/{entry.tempoDen} disagrees with reference * {entry.speedNum}/{entry.speedDen}"]
            let rep : RepStatus := {
              name := entry.name
              kind := "midi"
              bars := 0
              barsValid := true
              soundingNotesCount := entry.notes.length
              equivToRef := equiv
              tempoOk := tempoOk
              augFactor := entry.augFactor
            }
            (rep, equivFails ++ tempoFails)
      let reps := evalResults.map (·.1)
      let allFailures := evalResults.foldl (fun acc pair => acc ++ pair.2) []
      let allBarsValid := reps.all (·.barsValid)
      let allEquiv := reps.all fun r => r.equivToRef && r.tempoOk
      let ok := refBarsOk && allBarsValid && allEquiv && allFailures.isEmpty && !ref.bars.isEmpty
      let barFailExtra := if ref.bars.isEmpty then ["Reference score has zero bars"] else []
      let failuresJson := String.intercalate "," ((barFailExtra ++ allFailures).map fun f => s!"\"{jsonEscape f}\"")
      let repsJson := String.intercalate "," (reps.map repToJson)
      let json :=
        "{" ++
          s!"\"ok\":{boolJson ok}," ++
          s!"\"all_bars_valid\":{boolJson (refBarsOk && allBarsValid)}," ++
          s!"\"reference\":\"{jsonEscape refEntry.name}\"," ++
          s!"\"checked_bars\":{ref.bars.length}," ++
          s!"\"sounding_notes\":{refSounding.length}," ++
          s!"\"total_ticks\":{totalScoreTicks ref}," ++
          s!"\"representations\":[{repsJson}]," ++
          s!"\"failures\":[{failuresJson}]" ++
        "}"
      (ok, json)

private partial def readStdinAllAux (stdin : IO.FS.Stream) (acc : String) : IO String := do
  let line ← stdin.getLine
  if line.isEmpty then return acc
  else readStdinAllAux stdin (acc ++ line)

private def readStdinAll : IO String := do
  let stdin ← IO.getStdin
  readStdinAllAux stdin ""

def main (args : List String) : IO UInt32 := do
  let text ←
    match args with
    | ["--input", path] => IO.FS.readFile path
    | [path] => IO.FS.readFile path
    | [] => readStdinAll
    | _ =>
        IO.eprintln "Usage: score_verifier [--input <bundle.txt>]"
        return 2
  let items := parseBundle text
  let (ok, json) := verifyBundle items
  IO.println json
  return (if ok then 0 else 1)

-- <!-- APAF Bioinformatics | VerifierMain.lean | Approved | 2026-11-15 -->
