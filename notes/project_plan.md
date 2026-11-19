---
author: Ignatius Pang
ai_assist: Claude Code (Claude Fable 5.2)
created: 2026-11-19
modified: 2026-11-19
purpose: Project plan — folder restructure, karaoke trainer rebuild, Playwright testing
---

> **Status (2026-11-19):** Stages 0 to 5 are done on branch `restructure-karaoke-trainer`. Differences from the plan as approved:
> the trainer's default export location is `data/output/sing_along_packs/`; the older browser tests in `tests/test_app.py`
> were moved onto the shared browser fixture; a short `PRODUCT.md` was added for the design skill.

# Plan: restructure SheetMusicReader, rebuild the karaoke trainer, test with Playwright

## Context

- 14 Python modules sit flat at the repo root beside input PDFs (`data/`), generated output (`digitized_scores/`, `sing_along_packs/`), notes and build output. Paths are hardcoded in ~10 modules and every test file has its own `sys.path` hack.
- A previous session built a karaoke trainer. It exists but is uncommitted, and its front end is ~1,050 lines of CSS/JS inside Python strings in `karaoke_trainer.py` (2,108 lines). Known defects: a burst of chords after pause/seek, the lyric DOM rebuilt every animation frame, per-frame linear searches, 500s on extraction errors. The main page's highlighting runs on a `setTimeout` chain that is not tied to the audio clock.
- Decisions made: **full Python package**, **plain HTML + JS (no build step)**, **backing music synthesised from the chart's chords**.

## Stage 0 — Safety checkpoint

- Create branch `restructure-karaoke-trainer` and commit the current working tree as-is (so `git mv` keeps history and the previous session's work is recoverable).
- Baseline: run the full suite once and record the result.
  `PATH="$HOME/.elan/bin:/opt/homebrew/bin:$PATH" /Users/ignatiuspang/anaconda3/bin/python -m pytest -q`

## Stage 1 — Folder restructure (behaviour unchanged, tests green before moving on)

Target layout:

```
sheet_music_reader/
  paths.py            # the ONLY place that knows data locations
  psalms_db.py
  omr/       vector_omr.py, omr_pointcloud.py, score_from_image.py, pdf_parser.py
  export/    score_formatter.py, audio_synth.py, lean_bridge.py
  karaoke/   extract.py (Python logic of karaoke_trainer.py), render.py (new, small)
  cli/       music_pipeline.py, digitize_all.py, load_psalm.py, benchmark_lilypond.py
  web/       app.py, templates/, static/
data/
  input/     psalms/*.pdf, Cantabile/, samples/test_s89.*, benchmark_corpus/original_ly/
  output/    digitized_scores/, sing_along_packs/, benchmark/{images,manifest,reports}
tests/  notes/  docs/  crates/  formalization/  scripts/  dist/
pyproject.toml        # [tool.pytest.ini_options] pythonpath=".", testpaths="tests"
```

Steps:
1. `git mv` everything into place; add `__init__.py` files. `docs/` stays (static wasm site). `CANTABILE_PLAN.md` and `music_engraving_specification.md` → `notes/`; skills zip → `dist/`.
2. `paths.py`: `REPO_ROOT`, `INPUT_DIR`, `PSALM_PDF_DIR`, `OUTPUT_DIR`, `SCORES_DIR`, `PACKS_DIR`, `BENCHMARK_DIR`, `LEAN_DIR`, `WASM_ENGRAVER_JS`. Replace every hardcoded path found in the inventory (`app.py:16`, `psalms_db.py:5`, `digitize_all.py:16`, `lean_bridge.py:35-37`, `vector_omr.py:963`, `score_from_image.py:767,1283`, `benchmark_lilypond.py:673,734-767`, `music_pipeline.py:597,618`) with these constants. CLI output defaults move under `data/output/`.
3. Rewrite imports to package form (`from sheet_music_reader.omr import vector_omr`). CLIs run as `python -m sheet_music_reader.cli.music_pipeline …`, the app as `python -m sheet_music_reader.web.app`.
4. Tests: delete the per-file `sys.path` hacks; add `tests/conftest.py` with `ROOT`/path fixtures and a shared `flask_server` fixture that polls `/api/health` instead of `sleep(2.0)`. Fix the two cwd-relative paths (`test_app.py` subprocess, `test_music_pipeline.py:146`).
5. Both copies of `musescore_helper.py` (`.claude/skills` and `.agents/skills`): update `parents[4]` imports to the package.
6. Hygiene:
   - `.gitignore`: add `formalization/lean/.lake/`, `data/output/**/work/`, `_omr_work/`.
   - Remove untracked `data/Ps-122-I-Rejoiced-Chart.pdf` — byte-identical (same md5) to tracked `04_Ps-122-I-Rejoiced-Chart.pdf` (AGENTS.md Rule 1); point the code/tests at the `04_` file.
   - Remove root `test_s89.pdf` duplicate of `docs/test_s89.pdf` only after moving one copy to `data/input/samples/`.
   - Delete stale `tests/puppeteer_test.js` (targets port 5000 and a removed flow).
7. Update path/command references in `README.md` (incl. structure tree), `AGENTS.md` + `.agents/AGENTS.md`, the 5 SKILL.md files, `notes/how_to_*.md`. Old handover notes are historical: left unchanged, with one line added at the top pointing to the new layout.
8. Gate: full pytest equals the Stage 0 baseline; `cd formalization/lean && lake build` still works.

## Stage 2 — Skill for this kind of app

No loadable skill covers "no-build HTML/JS trainer inside Flask + Playwright" (`impeccable` covers visual design only; the React-dashboard and Playwright skills live in `~/.gemini` and are not loadable here).

- Create `.claude/skills/web-trainer-app/SKILL.md` (copy to `.agents/skills/`), following the project's existing skill conventions (frontmatter, `<!-- APAF Metadata -->` block, APAF footer). Contents: file layout, the classic-script namespace convention, the audio-clock scheduling pattern, how the standalone file is inlined, the Playwright recipe (fixtures, zero-console-error assertion, screenshots), and a checklist.
- Load it, plus `impeccable` for the visual design pass.
- Note: the global `/orchestrate build` workflow is R-only (Rscript hooks in another repo) and cannot run here; its requirements that do apply (watermark, metadata placement, no `for` loops over data) are followed.

## Stage 3 — Karaoke trainer rebuild

**Python (`sheet_music_reader/karaoke/`)**
- `extract.py`: existing extraction logic moved unchanged (schema stays: modes → phrases → bars → events / words / chords). Only remove unused imports and the private cross-module calls.
- `render.py`: ~60 lines. `render_standalone(data)` reads the template + CSS + JS files and inlines them with the score JSON, so the offline `file://` trainer and the Flask page share one source.
- `web/app.py`: `/karaoke` renders `templates/karaoke.html`; karaoke API routes return 400 with a message on extraction failure.

**Front end (`web/templates/karaoke.html`, `web/static/css/karaoke.css`, `web/static/js/karaoke/`)**
Classic scripts on one `window.Karaoke` namespace (ES modules do not load from `file://`):
- `timeline.js` — builds once per mode: sorted event/word/chord arrays and binary-search lookups by time.
- `audio.js` — WebAudio: vocal guide, bass + chord backing, click; three gain buses; lookahead scheduler driven only by `audioCtx.currentTime`. Seek recomputes all cursors by binary search (fixes the chord burst).
- `stage.js` — the karaoke view. Per phrase, one shared column grid: **each note is drawn on the 5-line staff directly above its syllable**; the active column lights the notehead and the word together, the word fills left-to-right over its duration, sung words stay tinted, a playhead moves across, the next phrase is shown dimmed below. DOM built once per phrase; per-frame work only toggles classes.
- `controls.js` — play/pause, restart, click-a-word to seek, mode (full psalm / as written / response / verse N), speed presets + BPM, count-in, loop current phrase, transpose, mixer sliders (vocal guide, backing, click), score picker and PDF upload in server mode, keyboard shortcuts.
- `piano.js` — small keyboard strip lighting the current pitch; note-name and chord pills.
- Staff drawing follows AGENTS.md Rule 2 order (lines, clef, key signature, time signature, bar line, notes).
- Main page (`index.html` / `app.js`): keep the now-singing strip and the Karaoke Trainer button; no rewrite of its playback engine in this pass.

**Outputs**: regenerate `data/output/sing_along_packs/Ps_122_Let_Us_Go_Rejoicing/Ps_122_Karaoke_Trainer.html`.

## Stage 4 — Playwright testing

Automated (`tests/test_karaoke_e2e.py`, Python sync API, headless Chromium, shared `flask_server` fixture):
- loads with zero console/page errors; score list populated; 6 modes for Psalm 122
- during playback the active notehead and active word carry the same event index, and that index advances over time
- note pill / chord pill match the data at the sampled time (e.g. first chord G, first word "Let")
- pause freezes position; resume continues without extra scheduled chords (count scheduled events through a test hook)
- clicking a word seeks there; loop repeats the phrase; mode switch and 50% speed change the timeline
- mixer sliders change the bus gain values; count-in delays the first note
- the standalone file opened via `file://` passes the same smoke test
- narrow viewport (390px) has no horizontal overflow

Interactive: drive the app with Playwright myself, capture screenshots at desktop and phone widths (start, mid-phrase, phrase change, after seek), review them, and fix what they show. Existing karaoke tests in `test_music_pipeline.py` / `test_app.py` are updated to the new paths and selectors (AGENTS.md Rule 4).

## Stage 5 — Wrap-up

- README: new structure tree, run commands, trainer section. `references.md`: no new URLs expected.
- Save the plan as `notes/project_plan.md` (global rule: keep a project plan document current).
- Final full pytest run; report exact pass/skip/fail counts and attach the screenshots' paths.
- Commits on the branch per stage; nothing pushed.

## Verification

1. `python -m pytest -q` → same or better than the Stage 0 baseline, plus the new E2E tests.
2. `python -m sheet_music_reader.web.app` → open `/karaoke`, play Psalm 122 full arrangement; Playwright screenshots show note + word highlighted in the same column.
3. Open the regenerated standalone HTML from `file://` with the server stopped.
4. `git status` shows no code at the repo root and no generated files outside `data/output/`.

<!-- APAF Bioinformatics | R_is_for_Robot | Approved -->
