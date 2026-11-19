"""Playwright tests for the Karaoke Trainer: note + word highlighting, backing music, controls.

All timing assertions read the app's own audio-clock position (window.Karaoke.debug),
so they wait on state rather than on fixed sleeps.
"""
import pytest

from sheet_music_reader.karaoke import extract, render
from sheet_music_reader.web.app import app as flask_app
from tests.conftest import PS122_PDF

POS = "window.Karaoke.debug.position()"
PS122 = "pdf:04_Ps-122-I-Rejoiced-Chart.pdf"


def open_trainer(page, base):
    page.goto(f"{base}/karaoke?score={PS122}")
    page.wait_for_selector("[data-testid=stage] .col", timeout=20000)
    page.wait_for_function("document.getElementById('songTitle').textContent.includes('Let us go')")


def play_without_count_in(page):
    page.uncheck("[data-testid=countin-toggle]")
    page.click("[data-testid=play]")
    page.wait_for_function(f"window.Karaoke.audio.isPlaying() && {POS} > 0")


def set_tempo(page, bpm):
    page.evaluate(
        """(bpm) => { const s = document.getElementById('tempoSlider'); s.value = bpm;
                      s.dispatchEvent(new Event('input', { bubbles: true })); }""",
        bpm,
    )


def test_trainer_loads_with_score_modes_and_staff_in_engraving_order(flask_server, page_with_errors):
    page, errors = page_with_errors
    open_trainer(page, flask_server)

    assert page.locator("[data-testid=karaoke-mode-tabs] .tab").count() == 6
    assert page.locator("[data-testid=karaoke-score-select] option").count() >= 15
    assert "G Major" in page.inner_text("[data-testid=song-meta]")
    assert page.locator("[data-testid=phrase-list] li").count() == 10
    assert page.inner_text("[data-testid=next-line]").startswith("Next: I re")

    # AGENTS.md Rule 2: staff lines, clef, key signature, time signature, bar line, then notes.
    xs = page.evaluate(
        """() => { const s = document.querySelector('svg.system');
            const left = (sel) => s.querySelector(sel).getBoundingClientRect().left;
            return { lines: s.querySelectorAll('.staffline').length, clef: left('path.ink'), key: left('.keysig'),
                     time: left('.timesig'), bar: left('.barline'), note: left('.col .head, .col.rest .ink') }; }"""
    )
    assert xs["lines"] == 5
    assert xs["clef"] < xs["key"] < xs["time"] < xs["bar"] < xs["note"]
    assert errors == []


def test_note_and_word_light_up_together_from_the_audio_clock(flask_server, page_with_errors):
    page, errors = page_with_errors
    open_trainer(page, flask_server)
    page.click("[data-testid=speed-25]")
    play_without_count_in(page)

    # First sung note of Psalm 122: "Let" on A4 over a G chord.
    page.wait_for_function(f"{POS} > 0.6")
    assert page.inner_text("#nowNote") == "A4"
    assert page.inner_text("#nowWord") == "Let"
    assert page.inner_text("#nowChord") == "G"
    active = page.locator(".col.active")
    assert active.count() == 1
    assert active.locator(".syllable").text_content() == "Let"
    assert float(active.locator("clipPath rect").get_attribute("width")) > 0  # the word is filling

    page.click("[data-testid=speed-100]")

    def snapshot():
        return page.evaluate(
            """() => { const r = window.Karaoke.debug.rendered, tl = window.Karaoke.app.state.tl;
                const ev = tl.eventAt(r.q), col = document.querySelector('.col.active');
                const sounding = ev && r.q < ev.onset_q + ev.dur_q ? ev : null;
                return { q: r.q, expected: sounding ? sounding.event_index : null, word: sounding ? sounding.word : null,
                         shownEv: col ? Number(col.dataset.ev) : null, shownWord: col ? Number(col.dataset.word) : null,
                         band: col ? getComputedStyle(col.querySelector('.band')).fill : null,
                         playheads: document.querySelectorAll('.playhead.on').length }; }"""
        )

    def sample(target):
        page.wait_for_function(f"{POS} > {target}")
        snap = snapshot()
        assert snap["shownEv"] == snap["expected"], snap
        assert snap["shownWord"] == snap["word"], snap
        assert snap["playheads"] == 1
        return snap["shownEv"]

    seen = list(map(sample, (2.0, 4.6, 7.2, 9.0)))
    assert seen == sorted(seen) and len(set(seen)) >= 3
    page.wait_for_function("document.querySelectorAll('.col.sung').length >= 5")
    assert errors == []


def test_pause_freezes_and_resume_does_not_burst(flask_server, page_with_errors):
    page, errors = page_with_errors
    open_trainer(page, flask_server)
    play_without_count_in(page)
    page.wait_for_function(f"{POS} > 7.6")  # several chords and notes are already behind us

    page.click("[data-testid=play]")
    paused_at = page.evaluate(POS)
    before = page.evaluate("Object.assign({}, window.Karaoke.debug.counts)")
    page.wait_for_timeout(300)
    assert page.evaluate(POS) == paused_at
    assert page.evaluate("window.Karaoke.debug.counts") == before
    assert page.inner_text("[data-testid=status]") == "Paused"

    page.click("[data-testid=play]")
    page.wait_for_function(f"{POS} > {paused_at + 0.3}")
    after = page.evaluate("window.Karaoke.debug.counts")
    assert after["backing"] - before["backing"] <= 1
    assert after["guide"] - before["guide"] <= 2
    assert errors == []


def test_clicking_a_word_jumps_there_without_replaying_earlier_chords(flask_server, page_with_errors):
    page, errors = page_with_errors
    open_trainer(page, flask_server)

    word = page.evaluate("window.Karaoke.app.state.tl.words[8]")
    page.locator(f".col[data-word='{word['order']}']").first.click()
    assert page.evaluate(POS) == pytest.approx(word["start_q"])
    page.wait_for_function("document.querySelectorAll('.col.sung').length >= 6")  # painted on the next frame

    play_without_count_in(page)
    before = page.evaluate("Object.assign({}, window.Karaoke.debug.counts)")
    later = page.evaluate("window.Karaoke.app.state.tl.phrases[2]")
    page.locator(f".phrase-btn[data-phrase='{later['order']}']").click()
    page.wait_for_function(f"{POS} > {later['start_q'] + 0.2} && {POS} < {later['start_q'] + 3}")
    after = page.evaluate("window.Karaoke.debug.counts")
    assert after["backing"] - before["backing"] <= 2
    assert "line 3 of 10" in page.inner_text("[data-testid=section-label]")
    assert errors == []


def test_repeat_this_line_loops_the_phrase(flask_server, page_with_errors):
    page, errors = page_with_errors
    open_trainer(page, flask_server)
    page.click("[data-testid=next-phrase]")
    phrase = page.evaluate("window.Karaoke.app.state.tl.phraseAt(window.Karaoke.debug.position())")
    assert phrase["order"] == 1
    page.check("[data-testid=loop-toggle]")
    set_tempo(page, 200)
    play_without_count_in(page)

    page.wait_for_function(f"{POS} > {phrase['end_q'] - 2}", timeout=15000)
    page.wait_for_function(f"{POS} < {phrase['start_q'] + 2}", timeout=15000)  # wrapped to the start
    assert page.evaluate(POS) >= phrase["start_q"]
    assert "line 2 of 10" in page.inner_text("[data-testid=section-label]")
    assert errors == []


def test_modes_speed_transpose_and_mixer_controls(flask_server, page_with_errors):
    page, errors = page_with_errors
    open_trainer(page, flask_server)

    page.click("[data-testid=mode-response]")
    assert page.locator("[data-testid=phrase-list] li").count() == 1
    assert page.evaluate("window.Karaoke.app.state.tl.total") == 12
    assert page.get_attribute("[data-testid=mode-response]", "aria-pressed") == "true"

    page.click("[data-testid=speed-50]")
    assert page.inner_text("[data-testid=tempo-out]") == "50% · 36 bpm"
    assert page.evaluate("window.Karaoke.audio.tempo()") == 36

    page.click("[data-testid=transpose-up]")
    page.click("[data-testid=transpose-up]")
    assert page.inner_text("[data-testid=transpose-out]") == "+2 semitones"

    page.evaluate(
        """() => ['guideVol', 'backingVol'].forEach((id, i) => { const s = document.getElementById(id);
            s.value = [0, 90][i]; s.dispatchEvent(new Event('input', { bubbles: true })); })"""
    )
    assert page.evaluate("window.Karaoke.debug.gains()") == {"guide": 0, "backing": 0.9, "click": 0.3}

    page.click("[data-testid=speed-100]")
    play_without_count_in(page)
    page.wait_for_function(f"{POS} > 0.6")
    assert page.inner_text("#nowNote") == "B4"  # A4 sounding two semitones higher
    assert errors == []


def test_count_in_clicks_one_bar_before_the_first_note(flask_server, page_with_errors):
    page, errors = page_with_errors
    open_trainer(page, flask_server)
    assert page.is_checked("[data-testid=countin-toggle]")
    page.click("[data-testid=play]")

    page.wait_for_function(f"window.Karaoke.audio.isPlaying() && {POS} < -0.5")
    page.wait_for_function("document.getElementById('status').textContent === 'Counting in…'")
    counts = page.evaluate("window.Karaoke.debug.counts")
    assert counts["click"] == 2 and counts["guide"] == 0 and counts["backing"] == 0  # 6/8 = two beats
    page.wait_for_function(f"{POS} > 0.7 && document.getElementById('status').textContent === 'Playing'")
    assert page.evaluate("window.Karaoke.debug.counts.guide") >= 1
    assert errors == []


def test_library_score_without_chart_pdf_also_plays(flask_server, page_with_errors):
    page, errors = page_with_errors
    open_trainer(page, flask_server)
    page.select_option("[data-testid=karaoke-score-select]", "psalm:psalm_104_spirit")
    page.wait_for_function("!document.getElementById('songTitle').textContent.includes('Let us go')")
    page.wait_for_selector("[data-testid=stage] .col .syllable")
    play_without_count_in(page)
    page.wait_for_function(f"{POS} > 1")
    assert page.locator(".col.active, .col.sung").count() >= 1
    assert errors == []


def test_phone_width_has_no_sideways_scroll(flask_server, phone_page_with_errors):
    page, errors = phone_page_with_errors
    open_trainer(page, flask_server)
    sizes = page.evaluate(
        """() => ({ doc: document.documentElement.scrollWidth, win: window.innerWidth,
                    widest: Math.max(...[...document.querySelectorAll('svg.system')].map((s) => s.getBoundingClientRect().right)),
                    lines: document.querySelectorAll('svg.system').length })"""
    )
    assert sizes["doc"] <= sizes["win"]
    assert sizes["widest"] <= sizes["win"]
    assert sizes["lines"] >= 2  # the phrase wraps instead of shrinking
    play_without_count_in(page)
    page.wait_for_function(f"{POS} > 1.2")
    assert page.locator(".col.active").count() == 1
    assert errors == []


def test_offline_single_file_trainer_opens_from_file_url(tmp_path, page_with_errors):
    page, errors = page_with_errors
    out = render.write_standalone(extract.extract_karaoke_score_from_pdf(PS122_PDF), tmp_path / "trainer.html")
    html = out.read_text(encoding="utf-8")
    assert "/static/" not in html and "<!-- APAF Bioinformatics |" in html

    page.goto(out.as_uri())
    page.wait_for_selector("[data-testid=stage] .col")
    assert page.locator("#serverTools").is_hidden()
    assert page.locator("[data-testid=karaoke-mode-tabs] .tab").count() == 6
    play_without_count_in(page)
    page.wait_for_function(f"{POS} > 1.2")
    assert page.inner_text("#nowWord") in ("us", "go")
    assert errors == []


def test_unreadable_scores_return_a_clear_error_not_a_crash():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        assert client.get("/api/karaoke/score/pdf:does-not-exist.pdf").status_code == 404
        assert client.get("/api/karaoke/score/pdf:../secret.pdf").status_code in (400, 404)
        import io

        res = client.post("/api/karaoke/upload", data={"pdf": (io.BytesIO(b"not a pdf"), "broken.pdf")})
        assert res.status_code == 400
        assert "Could not read this score" in res.get_json()["error"]


# <!-- APAF Bioinformatics | test_karaoke_e2e.py | Approved | 2026-11-19 -->
