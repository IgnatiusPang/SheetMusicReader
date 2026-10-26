---
author: Ignatius Pang
ai_assist: Claude Code (Claude Opus 5.5)
created: 2026-10-25
purpose: Tutorial — turn a photo or scan of a printed score into an engraved PDF with score_from_image.py
---

# How to convert a score image into a clean PDF (`score_from_image.py`)

One command turns a photo, a scan, or a scanned PDF of printed music into:

| File | What it is |
| --- | --- |
| `<name>.pdf` | The engraved score, with the same line breaks as the original |
| `<name>.midi` | Playback of the same music |
| `<name>.ly` | LilyPond source. This is the master copy: edit it to correct anything, then rebuild |
| `<name>_review.pdf` | Proof sheet: each photographed line above its engraving, with bars that need checking flagged in red |
| `report.json` | What every stage did: bar checks, marks added, Claude corrections and cost |
| `<name>.homr.musicxml` | The raw note-reading result, which can be opened in MuseScore if preferred |

If the PDF came from notation software (Sibelius, MuseScore, Finale), don't use this tool. Use
`vector_omr.py` instead, which reads the notes exactly (see `notes/how_to_convert_score_to_midi.md`). To tell
which kind of PDF you have, run `pdffonts file.pdf`: a music font such as Opus, Leland or Bravura means a vector
score.

## 1. One-time setup (already done on this Mac)

| Piece | Where | Installed with |
| --- | --- | --- |
| Python env `omr` | `/Users/ignatiuspang/anaconda3/envs/omr` | `conda create -n omr python=3.12`, then `pip install homr music21 anthropic scikit-image pillow mido pytest` |
| homr (reads the notes) | inside the `omr` env | `pip install homr` (references.md item 10). Its models download on the first run |
| Audiveris (reads bowings and dynamics) | `~/Applications/Audiveris.app` | Download the macOS DMG (references.md item 11), accept the licence, and copy the app. Override the location with `--audiveris PATH` or the `AUDIVERIS` environment variable |
| LilyPond 2.26 (engraving) | `/opt/homebrew/bin/lilypond` | `brew install lilypond` |
| poppler (only for PDF scans) | `pdftoppm` | `brew install poppler` |
| Claude API key (optional) | environment | `export ANTHROPIC_API_KEY=...` (references.md item 12) |

Always run the tool with the env's interpreter. The base Anaconda and Homebrew Pythons lack homr:

```
PY=/Users/ignatiuspang/anaconda3/envs/omr/bin/python
```

## 2. Convert

The free pipeline uses homr and Audiveris:

```
$PY score_from_image.py convert data/Cantabile/cantabile.jpeg \
    --title "Cantabile" --composer "Charles Dancla" --instrument violin
```

For the most accurate result, add the Claude pass. It needs an API key and costs roughly a few cents to a dollar
per page:

```
$PY score_from_image.py convert data/Cantabile/cantabile.jpeg --refine claude --instrument violin
```

Output goes to `digitized_scores/from_image/<name>/` unless you pass `--out DIR`. Several images in one call
are converted one by one. A scanned PDF is rasterised at 300 dpi, and its pages are joined into one score.

| Option | Use it when |
| --- | --- |
| `--refine claude` | You want the markings (fingerings, all bowings, dynamics, hairpins, *cresc.*/*riten.* text) and note errors fixed |
| `--model ID` | You want a different Claude model (default `claude-opus-5-5`) |
| `--title`, `--composer` | You want to set the header. Without `--refine claude`, the title defaults to the file name |
| `--tempo 88` | You want to set the MIDI speed (quarter notes per minute). Default is the printed mark, else 90 |
| `--instrument violin` | You want a different MIDI sound; any General MIDI name LilyPond knows works, e.g. `"string ensemble 1"` |
| `--no-audiveris` | You want to skip the markings pass, which is faster |
| `--audiveris-marks bowing,dynamics,hairpins,fermata` | You want to choose which Audiveris markings to trust (see section 5) |
| `--keep-homr-ornaments` | You want homr's trills and breath marks, which it invents on photos, so they are off by default |

The terminal prints one summary per file:

```
cantabile.jpeg: 41 bars, 2 suspect, 0 pickup/closing, audiveris marks 19
  -> digitized_scores/from_image/cantabile/cantabile.pdf
  -> review digitized_scores/from_image/cantabile/cantabile_review.pdf
```

## 3. Proof-read

1. **Open `<name>_review.pdf`.** Each block shows the straightened photo line, with the engraving underneath. A
   red heading such as `CHECK bars [24]` and a red **?** over a bar mean its notes don't add up to the time
   signature. Every bar number is printed, so you can compare bar by bar.
2. **Read `report.json`.**
   - `bars.suspect` lists the flagged bars.
   - `audiveris.parts[].marks_added` counts the markings Audiveris added.
   - `claude.systems[]` gives each line's corrections (`log`), whether Claude's answer was used (`accepted`), and
     anything rejected (`problems`). It also records the cost in `cost_usd`.
3. **Fix what is wrong in `<name>.ly`.**
   - Each bar sits on its own line, ending with `% bar N`.
   - Pitches are absolute: `c'` is middle C and `fis''` is the F♯ an octave and a half above.
   - Durations: `4` is a crotchet (quarter note), `8` a quaver (eighth note), `4.` a dotted crotchet.
   - Markings follow the note: `\downbow`, `-3` (fingering), `\p`, `\<` … `\!`, `(` … `)`.
4. **Rebuild** with `lilypond -dno-point-and-click -o digitized_scores/from_image/<name>/<name> digitized_scores/from_image/<name>/<name>.ly`,
   which rewrites the PDF and the MIDI.

Pencil and handwriting are ignored. homr was trained on printed music. Claude is told to transcribe only printed
engraving. Audiveris reads only the darkest ink.

## 4. Measure accuracy against a trusted version

When a correct MIDI or MusicXML exists, compare note by note:

```
$PY score_from_image.py compare digitized_scores/from_image/cantabile/cantabile.midi digitized_scores/cantabile.midi
```

The output reports `pitch_accuracy` (right notes) and `full_accuracy` (right notes with right lengths).

## 5. What to expect

Measured on `data/Cantabile/cantabile.jpeg`, a phone photo with pencil marks and a curved page, against the
hand-verified `digitized_scores/cantabile.ly`:

| Stage | Result |
| --- | --- |
| homr notes | 171/171 pitches right (100%), 95.9% pitch and duration, 41/41 bars, 9/9 lines |
| Audiveris down-bows | 10 found, all correct, out of 20 printed |
| Audiveris dynamics | 5 of 7 correct (one *p* lands a bar late, and *cresc.* is read as *ff*) |
| Audiveris fermata, accent, tenuto, staccato | 19 found, all false (pencil dots), so they are off by default |
| Audiveris fingerings | 0 of 48 |
| Whole run without Claude | about 30 s |

So the free pipeline gives correct notes and partial markings. Fingerings, the remaining bowings, hairpins and
text directions need `--refine claude` or a manual edit of the `.ly`. The Claude pass sends each straightened
line, split into two magnified halves, with the draft. Answers that are malformed or make bars not add up are sent
back once with the errors; an answer that is still worse than the draft is discarded, so the draft is kept for that
line.

> The Claude pass has been tested with a simulated client (validation, retry, splicing) but not yet against the
> live API on this machine, because no key was set up when it was written. On its first real run, check
> `report.json` → `claude` and the review PDF.

## 6. Known limits

- **Only the top voice is kept** on a staff carrying two voices. Chord notes in one voice are kept.
- **Multi-staff music:** the tool engraves a piano or ensemble score as one group. homr numbers the staves part
  by part, which is assumed when matching photo lines to engraved lines. If the line images don't line up,
  review strips and the Claude pass are skipped, and `report.json` says so.
- **Tuplets** are re-grouped as `\tuplet 3/2` only for triplets. Other tuplets print as scaled durations.
- **Repeats and voltas** are not read as repeat structure; they engrave as plain bars.
- **Lyrics** and chord symbols are not read.
- **Bars that don't add up** still engrave, with the bar length adjusted so later bar lines stay in place. They
  are flagged in the review PDF and need a manual fix.

## 7. Where things are in the code

| Stage | Function in `score_from_image.py` |
| --- | --- |
| homr run that keeps the straightened staves | `run_homr`, `strips_by_system` |
| MusicXML into the internal model (`Score` → `Part` → `Bar` → `Ev`) | `from_musicxml` |
| Audiveris page, run and mark merge | `flat_page`, `run_audiveris`, `merge_marks`, `audiveris_pass` |
| Claude prompt, schema, retry and header | `REFINE_PROMPT`, `SYSTEM_SCHEMA`, `refine_system`, `refine_header`, `claude_pass` |
| Bar validation | `bar_check`, `suspect_bars` |
| Unmatched slur and hairpin clean-up | `fix_pairs`, `tidy` |
| LilyPond writer | `events_text`, `part_music`, `lilypond_source` |
| Review PDF | `review_pdf` |
| Accuracy check | `note_sequence`, `compare` |

Tests: `$PY -m pytest tests/test_score_from_image.py` (27 tests, including an end-to-end run on the cantabile
photo). The project rule of no imperative `for` loops applies here too: use `map`, `filter`, `reduce` or numpy.

<!-- APAF Bioinformatics | R_is_for_Robot | Approved -->
