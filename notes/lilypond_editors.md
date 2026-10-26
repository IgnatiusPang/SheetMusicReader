---
author: Ignatius Pang
created: 2026-10-26
purpose: Reference guide for popular open-source GNU LilyPond editors and editing environments
---

# Popular Open-Source LilyPond Editors

A guide to the most popular, actively maintained open-source editors and toolchains for GNU LilyPond sheet music engraving.

---

## 1. Frescobaldi (The Gold Standard)

* **License:** GPL-2.0+ (Open Source, Python 3 & PyQt5/PyQt6)
* **Website / Repo:** Referenced in [references.md (Item 13)](file:///Users/ignatiuspang/Workings/2026/SheetMusicReader/references.md#L50-L54)
* **Platforms:** macOS, Linux, Windows

### Key Features
* **Two-Way Point-and-Click (SyncTeX):** Clicking any musical symbol (notehead, rest, dynamic, barline) in the rendered PDF viewer instantly jumps the text editor cursor to the corresponding line and column in the `.ly` source. Control-clicking in the text editor highlights the corresponding element in the PDF preview.
* **Synchronized Audio & MIDI Playback:** Bundled MIDI playback engine tracks along with score playback, advancing an on-screen cursor across the PDF measures in real time.
* **Score Setup Wizard:** Step-by-step graphical dialog to define title, composer, key signatures, time signatures, instrument parts, staves, and lyrics into clean boilerplate code.
* **Music Manipulation Tools:**
  - Automatic key transposition (e.g., concert pitch to B♭ or E♭).
  - Rhythm transform (doubling or halving note durations).
  - Pitch re-pitching (applying new pitches to existing rhythmic durations).
  - Hyphenation helper for vocal/choral lyrics.
  - Automatic LilyPond syntax indentation and formatting.

### Installation on macOS
```bash
brew install --cask frescobaldi
```

---

## 2. Denemo (Visual / Keyboard WYSIWYG)

* **License:** GPL-3.0 (Open Source, C & GTK)
* **Website / Repo:** Referenced in [references.md (Item 14)](file:///Users/ignatiuspang/Workings/2026/SheetMusicReader/references.md#L55-L59)
* **Platforms:** macOS, Linux, Windows

### Key Features
* **Visual Notation with LilyPond Backend:** Edits visually on staff lines while generating parallel GNU LilyPond markup behind the scenes.
* **Rapid Multi-Modal Entry:**
  - Computer keyboard input: Letter keys for pitch (`C`, `D`, `E`...) and number keys for duration (`4` for quarter, `2` for half, `1` for whole).
  - MIDI controller keyboard input.
  - Microphone acoustic pitch recognition.
* **Snippet & Directive Insertion:** Allows embedding raw LilyPond Scheme expressions and formatting directives directly into measures.

### Installation on macOS
```bash
brew install --cask denemo
```

---

## 3. Visual Studio Code + LilyPond Suite

* **License:** MIT / Open Source
* **Platforms:** macOS, Linux, Windows (VS Code / VSCodium)

### Key Extensions
* **`lhl2617.lilypond` (VSLilyPond / LilyPond Suite):** Full syntax highlighting, snippet library, auto-completion, and command palette integration for `lilypond` compilation.
* **`tomoki1207.pdf` (VS Code PDF Viewer):** Side-by-side SVG/PDF display with SyncTeX point-and-click back to source lines.

### Installation
```bash
code --install-extension lhl2617.lilypond
```

---

## 4. Hacklily (Web-Based Collaborative Editor)

* **License:** AGPL-3.0 (Open Source, TypeScript & React)
* **Website / Repo:** Referenced in [references.md (Item 15)](file:///Users/ignatiuspang/Workings/2026/SheetMusicReader/references.md#L60-L64)
* **Platforms:** Browser-based (Zero local installation)

### Key Features
* Real-time side-by-side editing and vector PDF rendering.
* In-browser WebAudio MIDI playback.
* Cloud sharing, versioning, and permalink generation.

---

## Comparison Summary

| Editor | Interface Paradigm | MIDI Playback | Point-and-Click | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Frescobaldi** | Text + Synchronized PDF | Yes (Score sync) | Two-way | Dedicated engraving & comprehensive scores |
| **Denemo** | Visual Notation (WYSIWYG) | Yes | Visual to `.ly` | Fast keyboard/MIDI entry without memorizing syntax |
| **VS Code + VSLilyPond** | Code Editor IDE | Optional via plugin | Two-way (with PDF viewer) | Programmers integrating LilyPond into Git/scripts |
| **Hacklily** | Web Application | Yes (WebAudio) | One-way | Quick testing, education, and cloud sharing |

---

<!-- APAF Bioinformatics | R_is_for_Robot | Approved -->
