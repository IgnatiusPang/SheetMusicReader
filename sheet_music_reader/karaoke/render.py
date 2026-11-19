"""Build the Karaoke Trainer page from the real template, CSS and JS files.

The Flask page and the offline single-file trainer share one source: the offline
file is the template with its stylesheet, scripts and score data inlined.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sheet_music_reader import paths

TEMPLATE = paths.TEMPLATES_DIR / "karaoke.html"
BOOT_RE = re.compile(r"window\.KARAOKE_BOOT = \{.*?\};")
LINK_RE = re.compile(r'<link rel="stylesheet" href="/static/([^"]+)">')
SCRIPT_RE = re.compile(r'<script src="/static/([^"]+)"></script>')


def _static_text(rel: str) -> str:
    return (paths.STATIC_DIR / rel).read_text(encoding="utf-8")


def _boot_line(data: dict[str, Any] | None, api_mode: bool) -> str:
    payload = json.dumps({"apiMode": api_mode, "data": data}).replace("</", "<\\/")
    return f"window.KARAOKE_BOOT = {payload};"


def render_page(data: dict[str, Any] | None = None, api_mode: bool = True) -> str:
    """Page as served by Flask: external CSS/JS, optional preloaded score."""
    html = TEMPLATE.read_text(encoding="utf-8")
    return BOOT_RE.sub(lambda _m: _boot_line(data, api_mode), html, count=1)


def render_standalone(data: dict[str, Any]) -> str:
    """One self-contained HTML file that opens from file:// with no server."""
    html = render_page(data, api_mode=False)
    html = LINK_RE.sub(lambda m: f"<style>\n{_static_text(m.group(1))}\n</style>", html)
    return SCRIPT_RE.sub(lambda m: f"<script>\n{_static_text(m.group(1))}\n</script>", html)


def write_standalone(data: dict[str, Any], out_html: Path) -> Path:
    out_html = Path(out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(render_standalone(data), encoding="utf-8")
    return out_html


# <!-- APAF Bioinformatics | render.py | Approved | 2026-11-19 -->
