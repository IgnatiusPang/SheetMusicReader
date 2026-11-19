
def test_homepage_loads(flask_server, chromium):
    with chromium.new_context() as context:
        page = context.new_page()
        page.goto(flask_server)
        
        # Verify page title and header elements
        assert "Psalm" in page.title()
        assert page.locator('[data-testid="psalm-select"]').is_visible()
        assert page.locator('[data-testid="score-view"]').is_visible()
        assert page.locator('[data-testid="piano-keyboard"]').is_visible()

def test_psalm_selection_and_lyrics_overlay(flask_server, chromium):
    with chromium.new_context() as context:
        page = context.new_page()
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

def test_playback_controls_and_keyboard_visualizer(flask_server, chromium):
    with chromium.new_context() as context:
        page = context.new_page()
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

def test_digitized_export_endpoints(flask_server, chromium):
    with chromium.new_context() as context:
        page = context.new_page()
        
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


def test_vocal_guide_speed_presets_and_lean_verify_ui(flask_server, chromium):
    with chromium.new_context() as context:
        page = context.new_page()
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


def test_main_page_links_to_karaoke_trainer(flask_server, chromium):
    """The score player keeps its now-singing strip and links to the trainer (full trainer tests: test_karaoke_e2e.py)."""
    with chromium.new_context() as context:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))

        page.goto(flask_server)
        page.wait_for_selector('[data-testid="karaoke-now-singing"]')
        page.click('[data-testid="open-karaoke-trainer"]')
        page.wait_for_selector('[data-testid="stage"] .col', timeout=15000)
        assert page.url.endswith("/karaoke")
        assert errors == []


# <!-- APAF Bioinformatics | test_app.py | Approved | 2026-11-15 -->
