# Music Engraving & Notation References

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-07-28 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

## Standard Music Notation & Engraving Reference Manuals

1. **Gould, Elaine**. *Behind Bars: The Definitive Guide to Music Notation*. Faber Music, 2011.
   - Comprehensive rules for staff systems, clef placement, key signatures, stem direction, beat-grouped pair beaming, tied note arcs, and lyric alignment.

2. **W3C MusicXML Specification (Version 4.0)**.
   - Standard XML schema for digital music notation exchange, score-partwise elements, clef, key, time, and note duration definitions.

3. **Standard Music Font Layout (SMuFL)**. W3C Music Notation Community Group.
   - Canonical glyph mapping for musical symbols including G-clef (`U+1D11E`), sharps (`U+266F`), flats (`U+266D`), quarter rests (`U+1D13D`), and half rests (`U+1D13C`).

4. **Read, Gardner**. *Music Notation: A Manual of Modern Practice*. Crescendo Publishing, 1979.
   - Notation standards for compound meters (`6/8`, `9/8`, `12/8`), diatonic coordinate mapping, and polyphonic chord alignment.

5. **GNU LilyPond**. *Music Engraving System (v2.26.0)*.
   - URL: `https://lilypond.org`
   - Release Asset: `https://gitlab.com/lilypond/lilypond/-/releases/v2.26.0`

6. **Dancla, Charles (arr. Samuel Applebaum)**. *Cantabile (Op. 130)*. AMEB Violin Syllabus, List A No. 1.
   - Reference: Belwin-Mills Publishing Corp. / Warner Chappell Music.

7. **AMEB Violin Series Performance - Cantabile (Dancla)**.
   - Video URL: `https://www.youtube.com/watch?v=fjnj9kXQPQA`

8. **AMEB Violin Series 8 Grade 2 List A No. 1 Tutorial - Dancla Cantabile**.
   - Video URL: `https://www.youtube.com/watch?v=ilxcLmLscAs`

9. **Cantabile by Charles Dancla - Violin Performance**.
   - Video URL: `https://www.youtube.com/watch?v=5sPs2-IE41E`

## Optical Music Recognition Engines (used by `score_from_image.py`)

10. **homr** — end-to-end OMR for camera photos (segmentation + transformer), AGPL-3.0. Installed with `pip install homr` (v0.7.0).
    - Repository: `https://github.com/liebharc/homr`

11. **Audiveris** — open-source OMR application (v5.11.0, AGPL-3.0); used for markings (bowings, dynamics, hairpins).
    - Releases: `https://github.com/Audiveris/audiveris/releases`

12. **Claude API** — vision model used by the optional `--refine claude` pass; credentials via `ANTHROPIC_API_KEY`.
    - Documentation: `https://platform.claude.com/docs`

## Popular Open-Source LilyPond Editors

13. **Frescobaldi** — The premier dedicated LilyPond sheet music editor (Python/PyQt, GPL-2.0+). Features two-way point-and-click PDF/source synchronization, MIDI playback, score wizard, and syntax tooling.
    - Official Website: `https://www.frescobaldi.org`
    - Repository: `https://github.com/frescobaldi/frescobaldi`

14. **Denemo** — Graphical WYSIWYG/WYSIWYM music notation editor with GNU LilyPond engraving backend (C/GTK, GPL-3.0). Supports acoustic and MIDI keyboard transcription.
    - Official Website: `http://www.denemo.org`
    - Repository: `https://git.savannah.gnu.org/cgit/denemo.git`

15. **Hacklily** — Modern open-source web-based LilyPond sheet music editor and sharing platform (TypeScript/React, AGPL-3.0).
    - Website: `https://www.hacklily.org`
    - Repository: `https://github.com/hacklily/hacklily`

## WebAssembly Music Engraving & Client-Side Engines

16. **Verovio** — Ultra-lightweight open-source music engraving library in C++ compiled to WebAssembly (`verovio-wasm`, LGPL-3.0). Renders MusicXML / MEI directly to resolution-independent SVG and vector PDF in the browser.
    - Official Website: `https://www.verovio.org`
    - Repository: `https://github.com/rism-digital/verovio`

17. **wasm-bindgen / wasm-pack** — Official Rust WebAssembly toolchain for high-performance browser deployment.
    - Repository: `https://github.com/rustwasm/wasm-pack`

18. **PDF.js** — General-purpose, web standards-based platform for parsing and rendering PDFs client-side in the browser.
    - Official Website: `https://mozilla.github.io/pdf.js/`
    - CDN: `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js`

19. **jsPDF** — Client-side solution for generating vector PDF documents in HTML5 and JavaScript.
    - Repository: `https://github.com/parallax/jsPDF`
    - CDN: `https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js`

## APAF Internal Repositories

20. **generalkeen** — Formal verification, transpile, and repair toolkit.
    - Repository: `https://github.com/APAF-bioinformatics/generalkeen`

21. **omegaheart** — GUI reactive verification and formal theorem catalog.
    - Repository: `https://github.com/APAF-bioinformatics/omegaheart`

22. **roar** — R to Rust transpilation, optimization, and parity verification.
    - Repository: `https://github.com/APAF-bioinformatics/roar`

23. **ouropy** — Python/R/Rust polyglot verification, dashboard, and metrics engine.
    - Repository: `https://github.com/APAF-bioinformatics/ouropy`

## Open-Source LilyPond Score Datasets & Training Corpora

24. **GNU LilyPond Regression & Benchmark Test Corpus**. LilyPond Official Test Suites (`input/regression`).
    - Repository: `https://gitlab.com/lilypond/lilypond`
    - GitHub Mirror: `https://github.com/lilypond/lilypond`

25. **Mutopia Project**. Free sheet music archive in GNU LilyPond format.
    - Repository: `https://github.com/MutopiaProject/MutopiaProject`
    - Website: `https://www.mutopiaproject.org`

---

<!-- APAF Bioinformatics | Sheet Music Reader | Approved -->


