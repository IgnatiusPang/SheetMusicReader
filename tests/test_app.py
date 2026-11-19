import os
import sys
import time
import subprocess
import socket
import pytest
from playwright.sync_api import sync_playwright

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

@pytest.fixture(scope="module")
def flask_server():
    """Starts Flask application server in background on free port for testing."""
    port = get_free_port()
    env = dict(os.environ)
    env["PORT"] = str(port)
    
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    time.sleep(2.0)
    yield f"http://127.0.0.1:{port}"
    proc.terminate()
    proc.wait()

def test_homepage_loads(flask_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(flask_server)
        
        # Verify page title and header elements
        assert "Psalm" in page.title()
        assert page.locator('[data-testid="psalm-select"]').is_visible()
        assert page.locator('[data-testid="score-view"]').is_visible()
        assert page.locator('[data-testid="piano-keyboard"]').is_visible()
        
        browser.close()

def test_psalm_selection_and_lyrics_overlay(flask_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(flask_server)
        
        page.wait_for_selector('[data-testid="psalm-select"]')
        
        # Verify psalm selector options loaded
        options = page.locator('[data-testid="psalm-select"] option').all()
        assert len(options) >= 15, f"Expected at least 15 psalms in dropdown, found {len(options)}"
        
        # Select psalm_103_kind_chart
        page.select_option('[data-testid="psalm-select"]', 'psalm_103_kind_chart')
        page.wait_for_timeout(500)
        
        # Verify psalm title and overlaid lyric words
        assert "Ps 103" in page.locator('[data-testid="psalm-title"]').text_content()
        assert page.locator('[data-testid="lyric-word-0"]').is_visible()
        assert "The" in page.locator('[data-testid="lyric-word-0"]').text_content()
        
        browser.close()

def test_playback_controls_and_keyboard_visualizer(flask_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(flask_server)
        
        page.wait_for_selector('[data-testid="play-btn"]')
        
        # Test Play button
        page.click('[data-testid="play-btn"]')
        page.wait_for_timeout(400)
        
        status_text = page.locator('[data-testid="status-indicator"]').text_content()
        assert "Playing" in status_text or "Ready" in status_text
        
        # Test Pause button
        page.click('[data-testid="pause-btn"]')
        page.wait_for_timeout(300)
        assert "Paused" in page.locator('[data-testid="status-indicator"]').text_content()
        
        # Test Stop button
        page.click('[data-testid="stop-btn"]')
        page.wait_for_timeout(300)
        assert "Stopped" in page.locator('[data-testid="status-indicator"]').text_content()
        
        browser.close()

def test_digitized_export_endpoints(flask_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Test MusicXML export
        res_xml = page.request.get(f"{flask_server}/api/psalms/psalm_103_kind_chart/export/musicxml")
        assert res_xml.status == 200
        assert "score-partwise" in res_xml.text()

        # Test MIDI export
        res_midi = page.request.get(f"{flask_server}/api/psalms/psalm_103_kind_chart/export/midi")
        assert res_midi.status == 200
        
        # Test JSON export
        res_json = page.request.get(f"{flask_server}/api/psalms/psalm_103_kind_chart/export/json")
        assert res_json.status == 200
        assert res_json.json()["id"] == "psalm_103_kind_chart"

        browser.close()


def test_vocal_guide_speed_presets_and_lean_verify_ui(flask_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))

        page.goto(flask_server)
        page.wait_for_selector('[data-testid="psalm-select"]')
        page.select_option('[data-testid="psalm-select"]', 'psalm_103_kind_chart')
        page.wait_for_timeout(400)

        assert page.locator('[data-testid="vocal-guide-toggle"]').is_checked()
        page.click('[data-testid="speed-preset-50"]')
        assert page.locator('#speedPercentLabel').text_content() == "50%"

        page.click('[data-testid="verify-lean"]')
        page.wait_for_function(
            "() => document.querySelector('[data-testid=\"lean-verify-badge\"]').textContent.includes('Lean: Verified')",
            timeout=10000,
        )

        res_ly = page.request.get(f"{flask_server}/api/psalms/psalm_103_kind_chart/export/lilypond?speed=0.5")
        assert res_ly.status == 200
        assert "\\version" in res_ly.text()

        res_wav = page.request.get(
            f"{flask_server}/api/psalms/psalm_103_kind_chart/export/wav?speed=0.5&voice=vocal_guide&count_in=0"
        )
        assert res_wav.status == 200
        assert res_wav.body().startswith(b"RIFF")
        assert errors == []

        browser.close()


def test_karaoke_trainer_note_word_and_chord_highlighting(flask_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))

        page.goto(flask_server)
        page.wait_for_selector('[data-testid="open-karaoke-trainer"]')
        page.wait_for_selector('[data-testid="karaoke-now-singing"]')

        page.goto(f"{flask_server}/karaoke")
        page.wait_for_selector('[data-testid="karaoke-current-line"] .karaoke-word', timeout=10000)
        assert "Let" in (page.locator('[data-testid="karaoke-current-line"]').text_content() or "")

        countin = page.locator('[data-testid="countin-toggle"]')
        if countin.is_checked():
            countin.uncheck()

        page.click('[data-testid="karaoke-play-btn"]')
        page.wait_for_timeout(900)

        note_text = page.locator('[data-testid="active-note-pill"]').text_content() or ""
        chord_text = page.locator('[data-testid="active-chord-pill"]').text_content() or ""
        assert note_text != "🎵 Ready"
        assert "--" not in chord_text
        assert page.locator(".karaoke-word.active, .karaoke-word.sung").count() >= 1

        page.click('[data-testid="karaoke-speed-50"]')
        assert page.locator("#ktSpeedVal").text_content() == "50%"

        page.click('[data-testid="karaoke-stop-btn"]')
        assert errors == []

        browser.close()


# <!-- APAF Bioinformatics | test_app.py | Approved | 2026-11-15 -->
