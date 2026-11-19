---
name: web-trainer-app
description: >-
  Build or change the browser practice trainers in this repo (karaoke note + word
  highlighting, background music, mixers, speed controls) as plain HTML, CSS and
  JavaScript with no build step, served by Flask and also exported as one offline
  HTML file, and test them with Playwright. Use for any work on
  sheet_music_reader/web/ or the karaoke trainer, and for any new interactive
  HTML or React-style practice app in this project.
---

<!-- APAF Metadata -->
<!-- last_verified_date: 2026-11-19 -->
<!-- apaf_approved: true -->
<!-- apaf_version: 1.0 -->
<!-- apaf_org: APAF Bioinformatics -->

# Web Trainer App (HTML + JS, no build step, Playwright-tested)

## Why no React and no bundler

The trainer must open from `file://` with no server and no internet, so that a singer can
keep one HTML file on a phone or laptop. That rules out CDN React (needs a connection) and
ES modules (browsers refuse `type="module"` from `file://`). Use classic scripts. If a future
app truly needs React, build it with Vite into `web/static/` and keep the same test recipe.

## Where things live

| What | Path |
|---|---|
| Score → timeline data (Python) | `sheet_music_reader/karaoke/extract.py` |
| Offline single-file export | `sheet_music_reader/karaoke/render.py` |
| Flask routes | `sheet_music_reader/web/app.py` (`/karaoke`, `/api/karaoke/*`) |
| Page | `sheet_music_reader/web/templates/karaoke.html` |
| Styles | `sheet_music_reader/web/static/css/karaoke.css` |
| Scripts | `sheet_music_reader/web/static/js/karaoke/*.js` |
| Browser tests | `tests/test_karaoke_e2e.py`, server fixture in `tests/conftest.py` |

## Rules

1. **One namespace.** Every script is an IIFE that adds to `window.Karaoke`. Load order is the
   order of the `<script>` tags in `karaoke.html`; `render.py` inlines them in that same order.
2. **One source for both versions.** Never write HTML, CSS or JS inside a Python string. The
   offline file is made by inlining the real files. After changing any of them, regenerate:
   `python -m sheet_music_reader.cli.music_pipeline karaoke <pdf> --out <html>`.
3. **The audio clock is the only clock.** Position in the song is always
   `(audioCtx.currentTime - startTime) * quartersPerSecond`. Never drive highlighting with
   `setTimeout` or `Date.now()`; they drift from the sound.
4. **Schedule ahead, in small slices.** A timer every ~25 ms schedules every sound that starts
   within the next ~120 ms. Each track (melody, chords, clicks) keeps a cursor into a sorted list.
5. **Seeking resets cursors by binary search** to the first item at or after the new position.
   Resetting a cursor to 0 replays every earlier chord at once.
6. **Build DOM once, then only toggle.** Draw a phrase when it becomes current. Per animation
   frame, change classes, the width of one clip rectangle (the word fill) and the playhead transform.
   Nothing else.
7. **Note above its word.** A note and its syllable are drawn in one `<g class="col">` that carries
   `data-ev` (event) and `data-word`. One class on that group (`active`, `in-word`, `sung`) colours both,
   so they can never disagree.
8. **Staff layout order** follows `AGENTS.md` Rule 2: lines, clef, key signature, time signature,
   bar line, notes.
9. **Loops.** Use `map`, `filter`, `reduce`, `forEach` for data. No `for` statements over data.
10. **Design.** Load the `impeccable` skill for visual work. Lyrics are the largest text on the
    page. Controls must work with a thumb at 390 px wide; the page must not scroll sideways.
11. **Test hooks.** `window.Karaoke.debug` exposes `position()`, `counts` (sounds scheduled per
    track), `gains()` and `rendered` (what the last frame drew). Tests read these; they stay in production.
12. **One browser per test session.** Use the `chromium`, `page_with_errors` and `flask_server` fixtures
    from `tests/conftest.py`. Starting a second `sync_playwright()` inside a test breaks the others.

## Playwright recipe

```python
def test_something(flask_server, page_with_errors):
    page, errors = page_with_errors
    page.goto(f"{flask_server}/karaoke")
    page.wait_for_selector("[data-testid=stage] .col")
    page.uncheck("[data-testid=countin-toggle]")
    page.click("[data-testid=play]")
    page.wait_for_function("window.Karaoke.debug.position() > 2")
    assert page.locator(".col.active").count() == 1
    assert errors == []
```

- Launch Chromium with `--autoplay-policy=no-user-gesture-required`; headless audio runs silently
  but the audio clock still advances.
- Wait on state with `wait_for_function`, never on fixed sleeps. The page repaints once per frame, so
  after an action wait for the DOM state you expect instead of reading it straight away.
- SVG text has no `inner_text`; read it with `text_content()`.
- Collect `page.on("pageerror")` and console errors; every test ends with `assert errors == []`.
- Test the offline file too: `page.goto(path.as_uri())`.
- Take screenshots at 1280×800 and 390×844 and look at them before calling the work done.
- Run: `python -m pytest tests/test_karaoke_e2e.py -q` (first time: `playwright install chromium`).

## Checklist before finishing

- [ ] Note and word light up together, in time with the sound, at 100% and 50% speed.
- [ ] Pause, resume, word-click seek and loop produce no burst of sound.
- [ ] Offline HTML regenerated and opens from `file://`.
- [ ] No console errors; no sideways scroll at 390 px.
- [ ] `python -m pytest` passes.

<!-- APAF Bioinformatics | SKILL.md | Approved | 2026-11-19 -->
