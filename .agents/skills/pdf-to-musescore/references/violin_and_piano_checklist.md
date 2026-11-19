<!-- APAF Metadata -->
<!-- last_verified_date: 2026-11-02 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

# Violin & Piano Double-Check Guide and MuseScore Tips

This reference accompanies [`pdf-to-musescore`](../SKILL.md). It lists the most common sheet-music conversion mistakes on violin and piano pieces, how to fix them quickly, and handy MuseScore shortcuts for teaching.

---

## 1. Common Conversion Traps (and How to Spot Them)

### Trap A: Key Signature Missing or Miscounted
- **What happens**: If a piece is in D Major (2 sharps: `F#` and `C#`) or G Major (1 sharp: `F#`), and the key signature is left as C Major (`<fifths>0</fifths>`), the bar math will still pass `verify`, but every `F` and `C` will sound a semitone flat.
- **How to check**: Look at Bar 1 right after the clef. Count the sharps (`#`) or flats (`b`) on the PDF and make sure the exact same number appears in MuseScore.
  - Sharps (`<fifths>`): `G = 1`, `D = 2`, `A = 3`, `E = 4`, `B = 5`.
  - Flats (`<fifths>`): `F = -1`, `Bb = -2`, `Eb = -3`, `Ab = -4`.

### Trap B: Dotted Note Read as a Plain Note (or Vice Versa)
- **What happens**: On scans or photos, the small dot after a dotted quarter note (`1.5` beats) is either missed (turning it into a `1.0`-beat quarter note) or invented from a speck on the paper.
- **How to check**: `musescore_helper.py verify` catches this automatically! It will report:
  `[Part P1, Bar 12] SUSPECT_SHORT: has 3.5 beats, expected 4 beats (-0.5 beats)`.
  Whenever a bar is short by `0.5` beats (or `0.25` beats), look in that bar on the PDF for a dotted note.

### Trap C: Violin Slurs Confused with Ties
- **What happens**: Curved lines connect notes in two ways:
  - A **tie** connects two notes of the *exact same pitch* so you hold the note without re-bowing or re-striking.
  - A **slur** connects notes of *different pitches* (meaning "play in one bow" on the violin, or "play legato" on the piano).
- **How to check**: If two different pitches have `<tie type="start"/>`, `verify` will flag an unclosed tie error. Make sure different pitches use `<slur>` and identical held pitches use `<tie>` + `<tied>`.

### Trap D: Violin Open-G3 Floor (`G3` = Lowest Playable Note)
- **What happens**: A smudge or lyric syllable below the violin staff gets read as a low `E3` or `D3` on ledger lines.
- **How to check**: A standard tuned violin cannot play below open `G3` (two ledger lines below the treble staff, `MIDI 55`). `verify --instrument violin` flags any note below `G3` automatically.

### Trap E: Piano Left-Hand Clef Switches (`Bass <-> Treble`)
- **What happens**: Piano pieces often start with the Left Hand in Bass Clef (`𝄢`), then print a small Treble Clef (`𝄞`) in the middle of bar 9 when the Left Hand moves up the keyboard. If the converter misses that small clef sign, the Left Hand notes in bar 9 will be read in Bass Clef—putting them nearly two octaves too low!
- **How to check**: On piano scores, scan the Left-Hand staff on the PDF for any small clef symbols printed inside a bar or at the start of a line.

### Trap F: Accidentals That Carry Through the Bar
- **What happens**: If bar 6 has an `F#` on beat 1 and another `F` on beat 4 on the same line/space without a natural sign (`♮`), that second `F` is *also* `F#`. In MusicXML, every note that sounds sharp must include `<alter>1</alter>` inside `<pitch>`, even if the sharp sign isn't printed a second time in the same bar.

---

## 2. Handy MuseScore Shortcuts for Teachers

Once you open any `.musicxml` file from the Slow Practice Pack in MuseScore:

| What you want to do | Shortcut / Menu in MuseScore |
| :--- | :--- |
| **Play / Pause** from the selected note | Click any note, then press **Spacebar** |
| **Loop a tricky 2-bar passage** | Click the first bar, **Shift + Click** the last bar, and click the **Loop** icon in the top playback bar |
| **Turn on the Metronome click** | Click the **Metronome** icon in the top playback bar (or use the built-in `Practice Click` part in our `33%` and `25%` files) |
| **Mute Left Hand, Right Hand, or Guide Click** | Press **F10** (Mixer) and click the **M** (Mute) or **S** (Solo) button on any staff |
| **Nudge the speed up or down on the fly** | Open the **Play** panel, or double-click the tempo text (`♩ = 45`) above Bar 1 and type a new number |
| **Print a clean copy with larger staves for young students** | Go to **Format → Page Settings** and increase **Staff space (sp)** slightly (e.g., from `1.75 mm` to `2.0 mm`) |

<!-- APAF Bioinformatics | violin_and_piano_checklist.md | Approved | 2026-11-02 -->

