"""Shared fixtures: repo paths and a live Flask server for browser tests."""
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PS122_PDF = ROOT / "data" / "input" / "psalms" / "04_Ps-122-I-Rejoiced-Chart.pdf"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _is_up(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1) as res:
            return res.status == 200
    except (urllib.error.URLError, OSError):
        return False


def _wait_until_up(url: str, proc: subprocess.Popen, deadline: float) -> None:
    if _is_up(url):
        return
    if proc.poll() is not None or time.monotonic() > deadline:
        raise RuntimeError(f"Flask server did not start: {url}")
    time.sleep(0.1)
    _wait_until_up(url, proc, deadline)


@pytest.fixture(scope="session")
def flask_server():
    """Start the Flask app on a free port and wait until /api/health answers."""
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "sheet_music_reader.web.app"],
        cwd=str(ROOT),
        env={**os.environ, "PORT": str(port)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        _wait_until_up(f"{base}/api/health", proc, time.monotonic() + 30)
        yield base
    finally:
        proc.terminate()
        proc.wait()


@pytest.fixture(scope="session")
def chromium():
    """One headless Chromium for the session; audio is allowed to start without a click."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        yield browser
        browser.close()


def _watch_errors(page) -> list:
    errors: list = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    return errors


@pytest.fixture
def page_with_errors(chromium):
    """A desktop page plus the list of page and console errors it has produced."""
    page = chromium.new_page(viewport={"width": 1280, "height": 800})
    yield page, _watch_errors(page)
    page.close()


@pytest.fixture
def phone_page_with_errors(chromium):
    page = chromium.new_page(viewport={"width": 390, "height": 844})
    yield page, _watch_errors(page)
    page.close()
