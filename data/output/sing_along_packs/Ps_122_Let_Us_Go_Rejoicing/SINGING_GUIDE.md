# Sing-Along Practice Guide: Ps 122(121) Let Us Go Rejoicing

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-11-15 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

**Composer / Arrangement:** A. Reefman  
**Key:** G Major (`1#` = F#)  
**Time Signature:** `6/8` — **6 eighth-note clicks per bar** (Click `1` is louder/higher; clicks `2-3-4-5-6` are softer)  
**Original Tempo:** dotted quarter = `48` BPM (`72` quarter BPM / `144` eighth clicks per minute)

---

## Karaoke Trainer (`Ps_122_Karaoke_Trainer.html`)

Open **`Ps_122_Karaoke_Trainer.html`** in Chrome, Safari or Edge. It works offline with no server. The same trainer is at `/karaoke` in the web app.

- **Note above its word.** Each line is shown as a staff with every note directly above its syllable. A yellow highlighter band marks the note and word being sung, the word fills in red as it is held, and words already sung turn grey-blue.
- **Background music.** Bass and chords from the chart play behind a guide melody. Three sliders set the guide melody, the background music and the beat click. Turn the guide melody down once you know the tune.
- **Practice controls.** Choose the full sung psalm, the printed chart, the response or a single verse. Speeds: 100%, 75%, 50%, 33%, 25%, or any tempo. "Repeat this line" loops one line; "Count me in" gives one bar of clicks first; "Key" moves the sound up or down by semitones.
- **Getting around.** Tap any word to jump to it. Space plays and pauses; the left and right arrow keys move one line.

---

## Which Folder Should I Play?

1. **`full_sung_arrangement/` (Recommended for singing through the whole Psalm)**  
   Plays the full liturgical structure:  
   **Response -> Verse 1 -> Response (with `"2. Je-"` pickup into Verse 2) -> Verse 2 -> Response -> Verse 3 -> Final Response** (`40` bars, `136` sounding notes).
2. **`chart_as_written/` (Bar-for-bar match with the printed page)**  
   Plays Bars `1-28` straight down the printed chart (`28` bars, `99` sounding notes) without repeating the Response between verses.

Every folder includes:
- `.mp3` and `.wav` **Vocal Guide + Background Chords** audio tracks (sustained vowel-like melody pitch + extracted harmony chord backing + 1-bar `6/8` count-in + beat clicks)
- `.pdf` printable sheet music engraved by GNU LilyPond at each practice tempo
- `.ly` (LilyPond), `.musicxml` (MuseScore), and `.mid` (MIDI) files
- `*_cert.lean` standalone Lean 4 kernel certificate verifying all bar lengths (`144` ticks per `6/8` bar), ties, pitch contours, and tempo ratios against the extracted PDF score

---

## Speed Ladder

| Edition | Speed | Dotted-Quarter Tempo | Click Speed (Eighths/min) | Use For |
|---|---|---|---|---|
| `*_speed_33pct` | `33%` (`1/3`) | `16` BPM | `48` clicks/min | Learning tricky rhythms and pitches word-by-word |
| `*_speed_50pct` | `50%` (`1/2`) | `24` BPM | `72` clicks/min | Comfortable slow sing-along and pitch locking |
| `*_speed_75pct` | `75%` (`3/4`) | `36` BPM | `108` clicks/min | Bridging toward full speed |
| `*_original` | `100%` (`1/1`) | `48` BPM | `144` clicks/min | Full service tempo |

---

## How to Count In and Enter Cleanly

Every audio file starts with **1 empty `6/8` count-in bar (6 clicks)**:  
**`ONE - 2 - 3 - 4 - 5 - 6`**

- **Response Entry (Bar 1):**
  - Click `1`: Breathe (`8th` rest)
  - Click `2`: Sing **`"Let"`**, click `3`: **`"us"`**, click `4`: **`"go"`** (held across clicks `4-5-6` into `1-2` of Bar 2)
- **Verse 1 Entry (`"I rejoiced..."`):**
  - Click `1`: Breathe (`8th` rest), click `2`: Sing **`"I"`**
- **Verse 2 Entry (`"2. Je - ru - sa - lem..."`):**
  - **In `full_sung_arrangement/`**: On the last bar of Response 2 (Bar 16), breathe on click `5` (`8th` rest) and sing **`"Je-"`** on click `6`, landing on **`"ru-"`** on click `1` of Bar 17!
  - **In `chart_as_written/`**: Bar 13 starts immediately on click `1` with **`"ru-sa-lem"`**.
- **Verse 3 Entry (`"For Israel's law..."`):**
  - Clicks `1-2`: Rest (`quarter` rest), click `3`: Sing **`"For"`**

---

## Suggested Practice Routine

1. Start with `full_sung_arrangement/Ps-122-I-Rejoiced-Chart_speed_50pct.mp3` (or `speed_33pct.mp3` for difficult bars). Follow along on the corresponding `*_speed_50pct.pdf`.
2. Hum with the Vocal Guide first, then sing words on your second pass.
3. Move up to `*_speed_75pct.mp3`, then finish at `*_original.mp3` (`100%`).

<!-- APAF Bioinformatics | SINGING_GUIDE.md | Approved | 2026-11-15 -->
