"""Vector-PDF optical music recognition: read notation-program PDFs glyph by glyph and write MIDI.

Works on PDFs exported by Sibelius (Opus font), MuseScore 2 (MScore font), MuseScore 3/4 (Leland/Bravura, SMuFL)
and Finale-style PostScript exports (Maestro-compatible TrueType). Pitch, accidentals, dots, flags, rests, clefs,
key and time signatures come straight from the music-font characters; stems, beams and ties are measured on a
288 dpi render because they are drawn as vector strokes rather than characters.

Pipeline (functional / vectorised, no imperative loops):
  page -> staves (5 equally spaced horizontal lines) -> systems (left barline joins) -> glyphs per staff
       -> events (chords / rests) with durations -> measures (bar lines) -> voice and triplet repair
       -> ties (render) -> lanes (staff index within system) -> MIDI, optional LilyPond proof

Usage:
  python vector_omr.py convert data/*.pdf --out digitized_scores/vector_midi [--proof DIR] [--report report.json]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, replace
from fractions import Fraction
from functools import lru_cache, partial, reduce
from itertools import chain
from pathlib import Path

import mido
import numpy as np
import pdfplumber
from PIL import Image

DPI = 288
PX = DPI / 72.0
DARK = 128
EPS = 1e-6

# ----------------------------------------------------------------------------- glyph tables
SMUFL = {
    0xE0A0: ("head", 8.0), 0xE0A2: ("head", 4.0), 0xE0A3: ("head", 2.0), 0xE0A4: ("head", 1.0),
    0xE260: ("acc", -1), 0xE261: ("acc", 0), 0xE262: ("acc", 1), 0xE263: ("acc", 2), 0xE264: ("acc", -2),
    0xE1E7: ("dot", None),
    0xE240: ("flag", 1), 0xE241: ("flag", 1), 0xE242: ("flag", 2), 0xE243: ("flag", 2), 0xE244: ("flag", 3), 0xE245: ("flag", 3),
    0xE4E3: ("rest", 4.0), 0xE4E4: ("rest", 2.0), 0xE4E5: ("rest", 1.0), 0xE4E6: ("rest", 0.5), 0xE4E7: ("rest", 0.25), 0xE4E8: ("rest", 0.125),
    0xE050: ("clef", "G"), 0xE052: ("clef", "G8vb"), 0xE053: ("clef", "G8va"), 0xE062: ("clef", "F"), 0xE05C: ("clef", "C"),
    0xE08A: ("timesym", (4, 4)), 0xE08B: ("timesym", (2, 2)), 0xE092: ("paren", "("), 0xE093: ("paren", ")"),
    **dict(map(lambda n: (0xE080 + n, ("digit", n)), range(10))),
}
# Sonata-compatible byte layout shared by Sibelius "Opus" and Finale "Maestro" style fonts.
SONATA = {
    0xCF: ("head", 1.0), 0xFA: ("head", 2.0), 0x77: ("head", 4.0), 0x57: ("head", 8.0),
    0x23: ("acc", 1), 0x62: ("acc", -1), 0x6E: ("acc", 0),
    0xAA: ("dot", None),
    0x6A: ("flag", 1), 0x4A: ("flag", 1), 0x72: ("flag", 2), 0x52: ("flag", 2),
    0xB7: ("rest", 4.0), 0xEE: ("rest", 2.0), 0xCE: ("rest", 1.0), 0xE4: ("rest", 0.5), 0xC5: ("rest", 0.25),
    0x26: ("clef", "G"), 0x56: ("clef", "G8vb"), 0x3F: ("clef", "F"), 0x42: ("clef", "C"),
    0x63: ("timesym", (4, 4)), 0x43: ("timesym", (2, 2)),
    **dict(map(lambda n: (0x30 + n, ("digit", n)), range(10))),
}
# MuseScore 2 legacy "MScore" font (codes observed in exported PDFs).
MSCORE = {
    0xE12D: ("head", 1.0), 0xE12C: ("head", 2.0), 0xE12B: ("head", 4.0), 0xE127: ("dot", None),
    0xE19E: ("clef", "G"), 0xE19C: ("clef", "F"),
    **dict(map(lambda n: (0x30 + n, ("digit", n)), range(10))),
}
CLEF_BOTTOM = {"G": 30, "G8vb": 23, "G8va": 37, "F": 18, "C": 24}   # diatonic index of the bottom staff line
CLEF_SHIFT = {"G8vb": -12, "G8va": 12}
STEP_SEMI = (0, 2, 4, 5, 7, 9, 11)
SHARP_ORDER = (3, 0, 4, 1, 5, 2, 6)
FLAT_ORDER = (6, 2, 5, 1, 4, 0, 3)
MUSIC_FONTS = ("Leland", "Bravura", "MScore", "Opus", "TTE")


def _byte(text: str) -> int | None:
    c = ord(text)
    if 0xF000 <= c <= 0xF0FF:
        return c - 0xF000
    if c < 0x80:
        return c
    try:
        return text.encode("mac_roman")[0]
    except UnicodeEncodeError:
        return None


def glyph_role(fontname: str, text: str) -> tuple[str, object] | None:
    if not text or not any(map(lambda f: f in fontname, MUSIC_FONTS)) or any(map(lambda f: f in fontname, ("Text", "Chords"))):
        return None
    if "Leland" in fontname or "Bravura" in fontname:
        return SMUFL.get(ord(text[0]))
    if "MScore" in fontname:
        return MSCORE.get(ord(text[0]))
    code = _byte(text[0])
    if "OpusSpecial" in fontname:                         # alternative black notehead Sibelius uses for verse pickups
        return ("xhead", 1.0) if code == 0x65 else SONATA.get(code) if code == 0xAA else None
    return SONATA.get(code) if code is not None else None


# ----------------------------------------------------------------------------- data classes
@dataclass(frozen=True)
class Glyph:
    role: str
    value: object
    x: float
    y: float
    w: float
    size: float


@dataclass(frozen=True)
class Staff:
    page: int
    lines: tuple
    x0: float
    x1: float

    @property
    def sp(self) -> float:
        return (self.lines[-1] - self.lines[0]) / 4

    @property
    def top(self) -> float:
        return self.lines[0]

    @property
    def bottom(self) -> float:
        return self.lines[-1]


@dataclass(frozen=True)
class Head:
    x: float
    y: float
    w: float
    base: float
    d: int
    midi: int
    stem: int          # +1 up, -1 down, 0 none
    beams: int
    dots: int
    value: float


@dataclass(frozen=True)
class Event:
    x: float
    value: float
    heads: tuple = ()          # empty = rest
    stem: int = 0
    tie: bool = False
    rest_y: float = 0.0
    extra: bool = False        # outside the bar count (Sibelius verse-pickup notes)

    @property
    def midis(self) -> tuple:
        return tuple(sorted(set(map(lambda h: h.midi, self.heads))))


@dataclass(frozen=True)
class Measure:
    events: tuple
    expected: float
    time: tuple
    key: int
    clef: str

    @property
    def total(self) -> float:
        return float(sum(map(lambda e: e.value, filter(lambda e: not e.extra, self.events))))

    @property
    def length(self) -> float:
        return float(sum(map(lambda e: e.value, self.events)))


@dataclass(frozen=True)
class StaffResult:
    staff: Staff
    measures: tuple
    key: int
    clef: str
    time: tuple
    notes: list = field(default_factory=list)


# ----------------------------------------------------------------------------- page primitives
def page_glyphs(page) -> list[Glyph]:
    def make(c: dict) -> Glyph | None:
        role = glyph_role(c["fontname"], c["text"])
        return None if role is None else Glyph(role[0], role[1], float(c["matrix"][4]), float(page.height - c["matrix"][5]),
                                                float(c["x1"] - c["x0"]), float(c["size"]))
    return list(filter(None, map(make, page.chars)))


TUPLET_RATIO = {2: 1.5, 3: 2 / 3, 4: 0.75, 5: 0.8, 6: 2 / 3}


def tuplet_glyphs(page) -> list[Glyph]:
    """Isolated digits 2-6 in a text font (tuplet numbers); digits touching other characters are chord or verse text."""
    chars = page.chars
    def isolated(c: dict) -> bool:
        return not any(map(lambda o: o is not c and abs(o["top"] - c["top"]) < 3 and o["text"].strip()
                           and (abs(o["x0"] - c["x1"]) < 2.0 or abs(c["x0"] - o["x1"]) < 2.0), chars))
    cand = filter(lambda c: c["text"] in "23456" and len(c["text"]) == 1 and isolated(c)
                  and (glyph_role(c["fontname"], c["text"]) is None or c["size"] < 12), chars)
    return list(map(lambda c: Glyph("tuplet", int(c["text"]), (c["x0"] + c["x1"]) / 2, (c["top"] + c["bottom"]) / 2,
                                    c["x1"] - c["x0"], c["size"]), cand))


def apply_tuplets(events: list, tuplets: list[Glyph], sp: float) -> list:
    """Scale the n events centred under each tuplet number by the tuplet ratio."""
    def window(t: Glyph) -> tuple | None:
        n = t.value
        if len(events) < n:
            return None
        centres = np.array(list(map(lambda e: e.x + (e.heads[0].w / 2 if e.heads else 0), events)))
        starts = np.arange(len(events) - n + 1)
        score = np.array(list(map(lambda i: abs(centres[i:i + n].mean() - t.x), starts)))
        i = int(starts[score.argmin()])
        span = centres[i + n - 1] - centres[i]
        ys = list(map(lambda h: h.y, chain.from_iterable(map(lambda e: e.heads, events[i:i + n]))))
        near = bool(ys) and min(map(lambda y: abs(y - t.y), ys)) < 7 * sp
        ok = score.min() < 1.5 * sp and span < 3.5 * n * sp and near and events[i].x - 1.5 * sp < t.x
        return (i, n) if ok else None
    wins = list(filter(None, map(window, tuplets)))
    scaled = dict(chain.from_iterable(map(lambda w: map(lambda j: (j, TUPLET_RATIO.get(w[1], 1.0)), range(w[0], w[0] + w[1])), wins)))
    return list(map(lambda ie: replace(ie[1], value=ie[1].value * scaled.get(ie[0], 1.0)), enumerate(events)))


def size_filter(glyphs: list[Glyph]) -> list[Glyph]:
    """Drop cue-size notes, braces and text-font look-alikes: keep glyphs near the dominant notehead size."""
    heads = np.array(list(map(lambda g: round(g.size, 1), filter(lambda g: g.role == "head", glyphs))))
    if heads.size == 0:
        return []
    vals, counts = np.unique(heads, return_counts=True)
    dom = float(vals[counts.argmax()])
    return list(filter(lambda g: 0.85 * dom <= g.size <= 1.2 * dom, glyphs))


def _segments(page, horizontal: bool) -> list[tuple]:
    objs = page.lines + page.rects
    if horizontal:
        keep = filter(lambda o: o["width"] > 40 and o["height"] < 1.5, objs)
        return list(map(lambda o: (o["x0"], o["x1"], (o["top"] + o["bottom"]) / 2), keep))
    keep = filter(lambda o: o["height"] > 6 and o["width"] < 4, objs)
    return list(map(lambda o: ((o["x0"] + o["x1"]) / 2, o["top"], o["bottom"]), keep))


def find_staves(page, page_index: int) -> list[Staff]:
    segs = sorted(_segments(page, True), key=lambda s: s[2])
    if not segs:
        return []
    ys = np.array(list(map(lambda s: s[2], segs)))
    groups = np.split(np.arange(len(segs)), np.flatnonzero(np.diff(ys) > 0.4) + 1)
    lines = list(filter(lambda l: l[2] - l[1] > 80, map(lambda g: (float(ys[g].mean()), min(map(lambda i: segs[i][0], g)),
                                                                     max(map(lambda i: segs[i][1], g))), groups)))
    if len(lines) < 5:
        return []
    ly = np.array(list(map(lambda l: l[0], lines)))
    win = np.lib.stride_tricks.sliding_window_view(ly, 5)
    gaps = np.diff(win, axis=1)
    ok = (gaps.min(axis=1) > 2.5) & (gaps.max(axis=1) < 12) & (gaps.std(axis=1) < 0.25)
    def pick(acc: list, i: int) -> list:
        return acc + [i] if ok[i] and (not acc or i >= acc[-1] + 5) else acc
    chosen = reduce(pick, range(len(win)), [])
    def make(i: int) -> Staff:
        sel = lines[i:i + 5]
        return Staff(page_index, tuple(map(lambda l: l[0], sel)), max(map(lambda l: l[1], sel)), min(map(lambda l: l[2], sel)))
    return list(map(make, chosen))


def group_systems(staves: list[Staff], verticals: list[tuple]) -> list[list[Staff]]:
    def joined(a: Staff, b: Staff) -> bool:
        x_left = min(a.x0, b.x0)
        return any(map(lambda v: x_left - 4 <= v[0] <= x_left + 6 and v[1] <= a.top + 1.5 and v[2] >= b.bottom - 1.5, verticals))
    def step(acc: list, s: Staff) -> list:
        return acc[:-1] + [acc[-1] + [s]] if acc and joined(acc[-1][-1], s) else acc + [[s]]
    return reduce(step, staves, [])


@lru_cache(maxsize=64)
def render(pdf_path: str, page_index: int) -> np.ndarray:
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "p"
        subprocess.run(["pdftoppm", "-r", str(DPI), "-gray", "-f", str(page_index + 1), "-l", str(page_index + 1),
                        pdf_path, str(prefix)], check=True, capture_output=True)
        img = next(Path(tmp).glob("p*.pgm"))
        return np.asarray(Image.open(img), dtype=np.uint8) < DARK


# ----------------------------------------------------------------------------- raster measurements
def _col(img: np.ndarray, x_pt: float, y0_pt: float, y1_pt: float) -> np.ndarray:
    x = int(round(x_pt * PX))
    a, b = sorted((int(round(y0_pt * PX)), int(round(y1_pt * PX))))
    a, b = max(a, 0), min(b, img.shape[0])
    return img[a:b, x] if 0 <= x < img.shape[1] and b > a else np.zeros(0, bool)


def _runs(col: np.ndarray) -> np.ndarray:
    """Lengths of consecutive True runs."""
    if col.size == 0:
        return np.zeros(0, int)
    edges = np.diff(np.concatenate(([0], col.astype(np.int8), [0])))
    return np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)


def stem_and_beams(img: np.ndarray, g: Glyph, sp: float) -> tuple[int, int, float]:
    """Stem direction (+1 up, -1 down, 0 none), beam count measured beside the stem near its tip, and stem x."""
    def best(xs: np.ndarray, y0: float, y1: float) -> tuple[float, float]:
        fr = np.array(list(map(lambda x: _col(img, x, y0, y1).mean() if _col(img, x, y0, y1).size else 0.0, xs)))
        return float(fr.max()), float(xs[fr.argmax()])
    up = best(np.arange(g.x + 0.55 * g.w, g.x + g.w + 0.15 * sp, 1.0 / PX), g.y - 1.9 * sp, g.y - 0.7 * sp)
    dn = best(np.arange(g.x - 0.15 * sp, g.x + 0.45 * g.w, 1.0 / PX), g.y + 0.7 * sp, g.y + 1.9 * sp)
    direction = 1 if up[0] >= dn[0] else -1
    frac, sx = (up if direction == 1 else dn)
    if frac < 0.85:
        return 0, 0, g.x + g.w / 2
    far = g.y - direction * 9 * sp
    col = _col(img, sx, g.y - direction * 0.6 * sp, far)
    col = col[::-1] if direction == 1 else col                      # ordered head -> far end
    gaps = np.flatnonzero(~col[:-1] & ~col[1:]) if col.size > 1 else np.zeros(0, int)
    length_px = int(gaps[0]) if gaps.size else col.size
    tip = g.y - direction * (0.6 * sp + length_px / PX)
    inner = g.y - direction * 1.2 * sp
    span_end = tip + direction * min(3.5 * sp, abs(inner - tip))
    def count(offset: float) -> int:
        runs = _runs(_col(img, sx + offset, tip - direction * 0.3 * sp, span_end))
        return int(((runs >= 0.3 * sp * PX) & (runs <= 1.3 * sp * PX)).sum())
    return direction, max(count(0.55 * sp), count(-0.55 * sp)), sx


def arc_fraction(img: np.ndarray, staff: Staff, xa: float, xb: float, y: float) -> float:
    """Fraction of columns between xa..xb holding a thin dark run just above or below y (a tie), staff/ledger rows masked."""
    if xb - xa < 0.3 * staff.sp:
        return 0.0
    sp = staff.sp
    ledger = np.array(list(staff.lines) + list(map(lambda k: staff.top - k * sp, range(1, 5))) + list(map(lambda k: staff.bottom + k * sp, range(1, 5))))
    xs = np.arange(xa, xb, 1.0 / PX)
    def band(y0: float, y1: float) -> float:
        rows = np.arange(int(y0 * PX), int(y1 * PX))
        rows = rows[(rows >= 0) & (rows < img.shape[0])]
        keep = rows[np.abs(rows[:, None] / PX - ledger[None, :]).min(axis=1) > 1.8 / PX]
        cols = np.clip((xs * PX).astype(int), 0, img.shape[1] - 1)
        block = img[np.ix_(keep, cols)] if keep.size else np.zeros((0, cols.size), bool)
        def thin(c: np.ndarray) -> bool:
            r = _runs(c)
            return bool(((r >= 1) & (r <= 0.35 * sp * PX)).any())
        return float(np.mean(list(map(thin, block.T)))) if block.size else 0.0
    return max(band(y - 2.2 * sp, y - 0.35 * sp), band(y + 0.35 * sp, y + 2.2 * sp))


# ----------------------------------------------------------------------------- staff reading
def diatonic_to_midi(d: int, alter: int) -> int:
    return 12 * (d // 7 + 1) + STEP_SEMI[d % 7] + alter


def key_alter(key: int, step: int) -> int:
    return (1 if step in SHARP_ORDER[:key] else 0) if key > 0 else (-1 if step in FLAT_ORDER[:-key] else 0)


def time_events(glyphs: list[Glyph], sp: float) -> list[tuple[float, tuple]]:
    """Time signatures in a staff as (x, (num, den)); parenthesised alternatives are ignored."""
    parens = sorted(map(lambda g: g.x, filter(lambda g: g.role == "paren", glyphs)))
    lefts = list(map(lambda g: g.x, filter(lambda g: g.role == "paren" and g.value == "(", glyphs)))
    rights = list(map(lambda g: g.x, filter(lambda g: g.role == "paren" and g.value == ")", glyphs)))
    inside = lambda x: any(map(lambda l: l < x, lefts)) and any(map(lambda r: x < r < x + 4 * sp, rights)) and \
        any(map(lambda l: x - 4 * sp < l < x, lefts))
    syms = list(map(lambda g: (g.x, g.value), filter(lambda g: g.role == "timesym", glyphs)))
    digits = sorted(filter(lambda g: g.role == "digit" and not inside(g.x), glyphs), key=lambda g: g.x)
    xs = np.array(list(map(lambda g: g.x, digits)))
    clusters = np.split(np.arange(len(digits)), np.flatnonzero(np.diff(xs) > 2 * sp) + 1) if digits else []
    def parse(idx: np.ndarray) -> tuple[float, tuple] | None:
        ds = list(map(lambda i: digits[i], idx))
        ys = sorted(set(map(lambda g: round(g.y / (sp * 0.6)), ds)))
        if len(ys) < 2:
            return None
        row = lambda r: int("".join(map(lambda g: str(g.value), sorted(filter(lambda g: round(g.y / (sp * 0.6)) == r, ds), key=lambda g: g.x))))
        num, den = row(ys[0]), row(ys[-1])
        return (ds[0].x, (num, den)) if 1 <= num <= 16 and den in (1, 2, 4, 8, 16) else None
    return sorted(syms + list(filter(None, map(parse, clusters))))


def read_staff(img: np.ndarray, staff: Staff, glyphs: list[Glyph], verticals: list[tuple], state: dict) -> StaffResult:
    sp = staff.sp
    clefs = sorted(map(lambda g: (g.x, g.value), filter(lambda g: g.role == "clef", glyphs)))
    tevents = time_events(glyphs, sp)
    heads_g = sorted(filter(lambda g: g.role in ("head", "xhead"), glyphs), key=lambda g: g.x)
    extra_x = set(map(lambda g: round(g.x, 1), filter(lambda g: g.role == "xhead", glyphs)))
    rests_g = list(filter(lambda g: g.role == "rest", glyphs))
    first_x = min(list(map(lambda g: g.x, heads_g + rests_g)) + list(map(lambda t: t[0], tevents)) + [staff.x1])
    clef_x = clefs[0][0] if clefs else staff.x0
    key_accs = list(filter(lambda g: g.role == "acc" and clef_x < g.x < first_x, glyphs))
    key = (len(list(filter(lambda g: g.value == 1, key_accs))) or -len(list(filter(lambda g: g.value == -1, key_accs))))
    key_end = max(list(map(lambda g: g.x + g.w, key_accs)) + [clef_x])
    clef_at = lambda x: (list(filter(lambda c: c[0] <= x + 0.5, clefs)) or [(0, state["clef"])])[-1][1]
    accs = list(filter(lambda g: g.role == "acc" and g.x > key_end + 0.1, glyphs))
    dots = list(filter(lambda g: g.role == "dot", glyphs))
    flags = list(filter(lambda g: g.role == "flag", glyphs))

    mid = staff.lines[2]
    def repeat_col(x: float) -> bool:
        col = list(filter(lambda d: abs(d.x - x) < 1.0, dots))
        return len(col) == 2 and all(map(lambda d: abs(abs(d.y - mid) - sp / 2) < 0.25 * sp, col))
    def n_dots(g: Glyph) -> int:
        """Augmentation dots: a horizontal chain starting just right of the glyph, repeat-sign dot pairs excluded."""
        xs = sorted(set(map(lambda d: round(d.x), filter(lambda d: g.x + 0.8 * g.w < d.x < g.x + g.w + 2.2 * sp
                                                         and abs(d.y - g.y) <= 0.75 * sp and not repeat_col(d.x), dots))))
        run = reduce(lambda acc, x: acc + [x] if (not acc and x < g.x + g.w + 1.2 * sp) or (acc and x - acc[-1] < 1.2 * sp) else acc, xs, [])
        return min(len(run), 2)

    def head(g: Glyph) -> tuple[Head, Glyph]:
        clef = clef_at(g.x)
        p = int(round((staff.bottom - g.y) / (sp / 2)))
        d = CLEF_BOTTOM[clef] + p
        acc = sorted(filter(lambda a: g.x - 2.6 * sp < a.x + a.w <= g.x + 0.25 * sp and abs(a.y - g.y) < 0.4 * sp, accs), key=lambda a: a.x)
        stem, beams, sx = stem_and_beams(img, g, sp) if g.value <= 2.0 else (0, 0, g.x)
        flag_n = max(list(map(lambda f: f.value, filter(lambda f: stem != 0 and abs(f.x - sx) < 1.6 and abs(f.y - g.y) < 5 * sp, flags))) + [0])
        n = max(beams, flag_n) if g.value == 1.0 else 0
        k = n_dots(g)
        value = g.value / (2 ** n) * (2 - 1 / 2 ** k)
        return Head(g.x, g.y, g.w, g.value, d, 0, stem, n, k, value), (acc[-1] if acc else None)

    raw = list(map(head, heads_g))
    rests = list(map(lambda g: Event(g.x, g.value * (2 - 1 / 2 ** n_dots(g)), (), 0, False, g.y), rests_g))

    # bar lines: verticals spanning the staff that are not stems
    def is_stem(v: tuple) -> bool:
        return any(map(lambda h: h[0].x - 0.8 <= v[0] <= h[0].x + h[0].w + 0.8 and v[1] - 2 * sp <= h[0].y <= v[2] + 2 * sp, raw))
    bars = sorted(set(map(lambda v: round(v[0], 1), filter(lambda v: staff.x0 - 1 <= v[0] <= staff.x1 + 1 and v[1] <= staff.top + 1.2
                                                         and v[2] >= staff.bottom - 1.2 and not is_stem(v), verticals))))
    bars = reduce(lambda acc, b: acc if acc and b - acc[-1] < 1.5 * sp else acc + [b], bars, [])
    bounds = [staff.x0 - 1] + list(filter(lambda b: b > first_x - 0.5 * sp, bars)) + [staff.x1 + 1]

    # accidentals persist to the end of the measure, keyed by diatonic position
    def measure_of(x: float) -> int:
        return int(np.searchsorted(np.array(bounds), x))
    def spell(acc: tuple, item: tuple) -> tuple:
        alters, out = acc
        h, acc_glyph = item
        mk = (measure_of(h.x), h.d)
        alter = acc_glyph.value if acc_glyph is not None else alters.get(mk, key_alter(key, h.d % 7))
        midi = diatonic_to_midi(h.d, alter) + CLEF_SHIFT.get(clef_at(h.x), 0)
        return {**alters, mk: alter}, out + (replace(h, midi=midi),)
    heads = list(reduce(spell, raw, ({}, ()))[1])

    # chords: same x (within a head width) and compatible stem
    def chord_step(acc: list, h: Head) -> list:
        if acc and abs(acc[-1][-1].x - h.x) < 0.8 * h.w and (acc[-1][-1].stem == h.stem or 0 in (acc[-1][-1].stem, h.stem)):
            return acc[:-1] + [acc[-1] + [h]]
        return acc + [[h]]
    chords = reduce(chord_step, sorted(heads, key=lambda h: (h.x, h.stem)), [])
    notes = list(map(lambda c: Event(min(map(lambda h: h.x, c)), max(map(lambda h: h.value, c)), tuple(c),
                                     max(map(lambda h: h.stem, c), key=abs),
                                     extra=all(map(lambda h: round(h.x, 1) in extra_x, c))), chords))
    events = apply_tuplets(sorted(notes + rests, key=lambda e: e.x), list(filter(lambda g: g.role == "tuplet", glyphs)), sp)

    def segment(i: int) -> tuple:
        return tuple(filter(lambda e: bounds[i] < e.x < bounds[i + 1], events))
    segs = list(filter(None, map(segment, range(len(bounds) - 1))))
    def time_at(x: float, current: tuple) -> tuple:
        prior = list(filter(lambda t: t[0] <= x, tevents))
        return prior[-1][1] if prior else current
    def build(acc: tuple, seg: tuple) -> tuple:
        measures, time = acc
        t = time_at(seg[0].x, time)
        expected = 4.0 * t[0] / t[1]
        fixed = tuple(sorted(repair(tuple(filter(lambda e: not e.extra, seg)), expected) + tuple(filter(lambda e: e.extra, seg)),
                             key=lambda e: e.x))
        return measures + (Measure(fixed, expected, t, key, clef_at(seg[0].x)),), t
    measures, time = reduce(build, segs, ((), state["time"]))
    return StaffResult(staff, measures, key, clef_at(staff.x1), time)


def repair(events: tuple, expected: float) -> tuple:
    """Fix over-full measures: whole rest = full bar, keep the upper voice, then apply triplets."""
    events = tuple(map(lambda e: replace(e, value=expected) if not e.heads and e.value == 4.0 and len(events) == 1 else e, events))
    total = sum(map(lambda e: e.value, events))
    if total <= expected + EPS:
        return events
    stems = set(map(lambda e: e.stem, filter(lambda e: e.heads, events)))
    if {1, -1} <= stems:
        upper = tuple(filter(lambda e: e.stem >= 0 if e.heads else True, events))
        if abs(sum(map(lambda e: e.value, upper)) - expected) > EPS:
            upper = tuple(filter(lambda e: e.heads, upper))
        if sum(map(lambda e: e.value, upper)) <= expected + EPS:
            return upper
        events = upper
    return triplets(events, expected)


def triplets(events: tuple, expected: float) -> tuple:
    excess = sum(map(lambda e: e.value, events)) - expected
    if excess <= EPS:
        return events
    cand = list(filter(lambda i: events[i].value == events[i + 1].value == events[i + 2].value
                       and events[i].value <= excess + EPS, range(len(events) - 2)))
    if not cand:
        return events
    i = cand[0]
    scaled = tuple(map(lambda e: replace(e, value=e.value * 2 / 3), events[i:i + 3]))
    return events[:i] + scaled[:2] + triplets(scaled[2:3] + events[i + 3:], expected - sum(map(lambda e: e.value, events[:i] + scaled[:2])))


# ----------------------------------------------------------------------------- whole score
@dataclass(frozen=True)
class Score:
    path: str
    systems: tuple          # tuple of tuple[StaffResult]
    tempo: float
    report: dict
    labels: tuple = ()      # tuple of Label resolved to (system, staff)


TEMPO_UNIT = {"\ueca5": 1.0, "\ueca3": 2.0, "\ueca7": 0.5, "\ueca2": 4.0, "\ueca9": 0.25,
              "q": 1.0, "h": 2.0, "e": 0.5, "w": 4.0, "x": 0.25}
TEMPO_DOT = ("\uecb7", "\ue1e7", ".", "k")


def tempo_of(pdf) -> float:
    """Quarter-note BPM from a metronome mark 'unit = N' (unit glyph from a music text font, optional dot)."""
    page = pdf.pages[0]
    def value(eq: dict) -> float | None:
        near = lambda c, lo, hi, dy: lo < c["x0"] < hi and abs(c["top"] - eq["top"]) < dy
        after = sorted(filter(lambda c: near(c, eq["x1"] - 0.5, eq["x1"] + 30, 5), page.chars), key=lambda c: c["x0"])
        text = "".join(map(lambda c: c["text"], after)).replace("\t", " ")
        m = re.match(r"\s*(\d+)", text)
        if not m:
            return None
        before = list(filter(lambda c: near(c, eq["x0"] - 45, eq["x0"], 10), page.chars))
        music = lambda c: any(map(lambda f: f in c["fontname"], ("LelandText", "BravuraText", "OpusText", "TTE", "Opus")))
        units = list(map(lambda c: TEMPO_UNIT[c["text"]], filter(lambda c: music(c) and c["text"] in TEMPO_UNIT, before)))
        dotted = any(map(lambda c: c["text"] in TEMPO_DOT and (music(c) or c["text"] == "."), before))
        return float(m.group(1)) * (units[-1] if units else 1.0) * (1.5 if dotted else 1.0)
    vals = list(filter(None, map(value, filter(lambda c: c["text"] == "=", page.chars))))
    return vals[0] if vals else 90.0


def read_score(pdf_path: Path) -> Score:
    with pdfplumber.open(pdf_path) as pdf:
        tempo = tempo_of(pdf)
        def page_systems(item: tuple) -> list:
            i, page = item
            staves = find_staves(page, i)
            vert = _segments(page, False)
            glyphs = size_filter(page_glyphs(page)) + tuplet_glyphs(page)
            def owner(g: Glyph) -> int | None:
                dist = np.array(list(map(lambda s: 0.0 if s.top <= g.y <= s.bottom else min(abs(g.y - s.top), abs(g.y - s.bottom)), staves)))
                j = int(dist.argmin()) if dist.size else -1
                return j if j >= 0 and dist[j] < 6 * staves[j].sp and staves[j].x0 - 30 <= g.x <= staves[j].x1 + 2 else None
            owners = list(map(owner, glyphs))
            per_staff = list(map(lambda j: list(map(lambda t: t[1], filter(lambda t: t[0] == j, zip(owners, glyphs)))), range(len(staves))))
            labels = list(filter(None, map(lambda lb: assign_label(lb, staves), page_labels(page, i))))
            return list(map(lambda sys: list(map(lambda s: (s, per_staff[staves.index(s)], vert, i, labels), sys)), group_systems(staves, vert)))
        raw_systems = sum(map(page_systems, enumerate(pdf.pages)), [])
    path = str(pdf_path)

    def read_system(acc: tuple, sys: list) -> tuple:
        out, states = acc
        def one(k_item: tuple) -> StaffResult:
            k, (staff, glyphs, vert, pi, _labels) = k_item
            st = {**states.get(k, {"clef": "G", "key": 0}), "time": states.get("time", (4, 4))}   # metre is score-wide
            return read_staff(render(path, pi), staff, glyphs, vert, st)
        results = list(map(one, enumerate(sys)))
        new_states = {**states, **dict(map(lambda kr: (kr[0], {"clef": kr[1].clef, "key": kr[1].key}), enumerate(results))),
                      "time": results[0].time if results else states.get("time", (4, 4))}
        return out + (tuple(results),), new_states
    systems, _ = reduce(read_system, raw_systems, ((), {}))
    systems = mark_ties(path, systems)
    where = dict(chain.from_iterable(map(lambda isys: map(lambda ks: (ks[1][0], (isys[0], ks[0])), enumerate(isys[1])), enumerate(raw_systems))))
    all_labels = list(chain.from_iterable(map(lambda sys: sys[0][4], raw_systems)))
    uniq = list(dict(map(lambda lb: ((lb.kind, lb.num, lb.staff), lb), all_labels)).values())
    placed = tuple(sorted(map(lambda lb: replace(lb, system=where[lb.staff][0], index=where[lb.staff][1]),
                              filter(lambda lb: lb.staff in where, uniq)), key=lambda lb: (lb.system, lb.index, lb.num)))
    score = Score(path, systems, tempo, report_of(systems), placed)
    return replace(score, report={**score.report, **structure_report(score)})


def mark_ties(path: str, systems: tuple) -> tuple:
    """Set Event.tie when a tie arc joins an event to the next same-pitch event in the same lane."""
    lanes = max(map(len, systems)) if systems else 0
    def lane_events(k: int) -> list:
        in_lane = filter(lambda isys: k < len(isys[1]), enumerate(systems))
        per_m = lambda si, sys: chain.from_iterable(map(lambda im: map(lambda ei: (si, im[0], ei), range(len(im[1].events))),
                                                        enumerate(sys[k].measures)))
        return list(chain.from_iterable(map(lambda isys: per_m(*isys), in_lane)))
    def tied(k: int, a: tuple, b: tuple) -> bool:
        ea = systems[a[0]][k].measures[a[1]].events[a[2]]
        eb = systems[b[0]][k].measures[b[1]].events[b[2]]
        common = set(ea.midis) & set(eb.midis)
        if not ea.heads or not eb.heads or not common:
            return False
        ha = next(filter(lambda h: h.midi in common, ea.heads))
        hb = next(filter(lambda h: h.midi in common, eb.heads))
        sa, sb = systems[a[0]][k].staff, systems[b[0]][k].staff
        img_a = render(path, sa.page)
        if a[0] == b[0]:
            return arc_fraction(img_a, sa, ha.x + ha.w + 0.45 * sa.sp, hb.x - 0.45 * sa.sp, ha.y) >= 0.7
        right = arc_fraction(img_a, sa, ha.x + ha.w + 0.45 * sa.sp, min(sa.x1, ha.x + ha.w + 3 * sa.sp), ha.y)
        left = arc_fraction(render(path, sb.page), sb, max(sb.x0, hb.x - 2.5 * sb.sp), hb.x - 0.45 * sb.sp, hb.y)
        return right >= 0.6 and left >= 0.5
    def lane_ties(k: int) -> set:
        seq = lane_events(k)
        return set(map(lambda i: seq[i], filter(lambda i: tied(k, seq[i], seq[i + 1]), range(len(seq) - 1))))
    ties = dict(map(lambda k: (k, lane_ties(k)), range(lanes)))
    def fix_staff(si: int, k: int, sr: StaffResult) -> StaffResult:
        def fix_measure(mi: int, m: Measure) -> Measure:
            return replace(m, events=tuple(map(lambda ie: replace(ie[1], tie=(si, mi, ie[0]) in ties[k]), enumerate(m.events))))
        return replace(sr, measures=tuple(map(lambda im: fix_measure(*im), enumerate(sr.measures))))
    return tuple(map(lambda isys: tuple(map(lambda ks: fix_staff(isys[0], ks[0], ks[1]), enumerate(isys[1]))), enumerate(systems)))


def report_of(systems: tuple) -> dict:
    measures = list(chain.from_iterable(map(lambda isys: chain.from_iterable(map(
        lambda ksr: map(lambda im: (isys[0], ksr[0], im[0], im[1]), enumerate(ksr[1].measures)), enumerate(isys[1]))), enumerate(systems))))
    over = list(filter(lambda t: t[3].total > t[3].expected + EPS, measures))
    under = list(filter(lambda t: t[3].total < t[3].expected - EPS, measures))
    fmt = lambda t: f"sys{t[0] + 1} staff{t[1] + 1} bar{t[2] + 1}: {t[3].total:g}/{t[3].expected:g}"
    first = systems[0][0] if systems else None
    return {
        "systems": len(systems), "staves": sum(map(len, systems)), "measures": len(measures),
        "notes": sum(map(lambda t: len(list(filter(lambda e: e.heads, t[3].events))), measures)),
        "key": first.key if first else None, "time": list(first.measures[0].time) if first and first.measures else None,
        "full": len(measures) - len(over) - len(under), "over": list(map(fmt, over)), "under": list(map(fmt, under)),
        "suspect": list(map(fmt, filter(lambda t: 0 < t[2] < len(systems[t[0]][t[1]].measures) - 1, under))) + list(map(fmt, over)),
    }


# ----------------------------------------------------------------------------- psalm structure
VERSE_WORD = re.compile(r"^(verse|vs\.?|v\.)$", re.I)
VERSE_JOINED = re.compile(r"^(?:verse|vs\.?|v\.)(\d{1,2})\.?$", re.I)
FINAL_WORD = re.compile(r"^(final|coda)$", re.I)
RESPONSE_WORD = re.compile(r"^(response|refrain|resp\.?|antiphon)$", re.I)
NUMBER = re.compile(r"^(\d{1,2})[.:]?$")


@dataclass(frozen=True)
class Label:
    kind: str                # "verse" | "response"
    num: int
    x: float
    y: float
    style: str               # "above" (boxed / VERSE caps), "side" (Vs., Verse, margin number)
    page: int
    staff: Staff | None = None
    system: int = -1
    index: int = -1


def page_labels(page, page_index: int) -> list[Label]:
    """Section labels: VERSE n / Verse n / Vs. n, boxed numbers, 'n.' at a lyric line start, Response/Refrain."""
    words = page.extract_words()
    def boxed(w: dict) -> bool:
        return any(map(lambda r: r["x0"] - 1.5 <= w["x0"] and r["x1"] + 1.5 >= w["x1"] and r["top"] - 1.5 <= w["top"]
                       and r["bottom"] + 1.5 >= w["bottom"] and r["width"] < 60 and r["height"] < 30, page.rects))
    def nxt(i: int) -> dict | None:
        w = words[i]
        cand = list(filter(lambda o: abs(o["top"] - w["top"]) < 3 and 0 <= o["x0"] - w["x1"] < 15, words))
        return cand[0] if cand else None
    def make(iw: tuple) -> Label | None:
        i, w = iw
        t, cy = w["text"], (w["top"] + w["bottom"]) / 2
        joined = VERSE_JOINED.match(t)
        if joined:
            return Label("verse", int(joined.group(1)), w["x0"], cy, "side", page_index)
        if VERSE_WORD.match(t):
            n = nxt(i)
            m = NUMBER.match(n["text"]) if n else None
            style = "above" if t.isupper() or boxed(w) else "side"
            return Label("verse", int(m.group(1)) if m else 0, w["x0"], cy, style, page_index)
        if RESPONSE_WORD.match(t):
            return Label("response", 0, w["x0"], cy, "above", page_index)
        if FINAL_WORD.match(t):
            return Label("final", 0, w["x0"], cy, "side", page_index)
        num = NUMBER.match(t)
        if num and boxed(w):
            return Label("verse", int(num.group(1)), w["x0"], cy, "above", page_index)
        if num and t.endswith("."):
            return Label("verse", int(num.group(1)), w["x0"], cy, "margin", page_index)
        return None
    return list(filter(None, map(make, enumerate(words))))


def assign_label(lb: Label, staves: list[Staff]) -> Label | None:
    """Attach a label to the staff it introduces; text far from any staff start (footers, lyrics) is dropped."""
    near_start = lambda s: lb.x <= s.x0 + 8 * s.sp
    if lb.style == "margin":                               # 'n.' must sit before the first lyric syllable
        hits = list(filter(lambda s: lb.x <= s.x0 + 2 * s.sp and s.bottom < lb.y <= s.bottom + 5 * s.sp, staves))
        return replace(lb, staff=hits[0]) if hits else None
    if lb.style == "side":
        hits = list(filter(lambda s: near_start(s) and s.top - 1.5 * s.sp <= lb.y <= s.bottom + 4.5 * s.sp, staves))
        if hits:
            return replace(lb, staff=hits[0])
    beside = list(filter(lambda s: lb.x < s.x0 + 2 * s.sp and s.top - 1.0 * s.sp <= lb.y <= s.bottom + 1.0 * s.sp, staves))
    if beside:
        return replace(lb, staff=beside[0])
    below = sorted(filter(lambda s: near_start(s) and 0 < s.top - lb.y <= 8 * s.sp, staves), key=lambda s: s.top)
    return replace(lb, staff=below[0]) if below else None


@dataclass(frozen=True)
class Section:
    kind: str                # "response" | "verse" | "score"
    num: int
    parts: tuple             # tuple of (system index, voice staff index, accompaniment staff indices tuple)


def sections_of(score: Score) -> list[Section]:
    """Response = systems before the first verse label (or from a Response label); verses = label to next label.
    A system with several verse labels (stacked verse staves) yields one verse per labelled staff."""
    verse = list(filter(lambda lb: lb.kind == "verse", score.labels))
    if not verse:
        return [Section("score", 0, tuple(map(lambda si: (si, 0, tuple(range(1, len(score.systems[si])))), range(len(score.systems)))))]
    by_sys = dict(map(lambda si: (si, list(filter(lambda lb: lb.system == si, score.labels))), range(len(score.systems))))
    def block_step(acc: list, si: int) -> list:
        labs = by_sys[si]
        vset = tuple(sorted(set(map(lambda lb: lb.num, filter(lambda lb: lb.kind == "verse", labs)))))
        if any(map(lambda lb: lb.kind == "response", labs)) and not vset:
            return acc + [("response", (), [si], {})]
        if any(map(lambda lb: lb.kind == "final", labs)) and not vset:
            return acc + [("final", (), [si], {})]
        if vset:
            staff_of = dict(map(lambda lb: (lb.num, lb.index), filter(lambda lb: lb.kind == "verse", labs)))
            if acc and acc[-1][0] == "verse" and len(vset) > 1 and acc[-1][1] == vset:
                kind, nums, sis, maps = acc[-1]
                return acc[:-1] + [(kind, nums, sis + [si], {**maps, si: staff_of})]
            return acc + [("verse", vset, [si], {si: staff_of})]
        if not acc:
            return [("response", (), [si], {})]
        kind, nums, sis, maps = acc[-1]
        return acc[:-1] + [(kind, nums, sis + [si], maps)]
    blocks = reduce(block_step, range(len(score.systems)), [])
    def expand(block: tuple) -> list[Section]:
        kind, nums, sis, maps = block
        if kind in ("response", "final"):
            return [Section(kind, 0, tuple(map(lambda si: (si, 0, tuple(range(1, len(score.systems[si])))), sis)))]
        first = maps[sis[0]]
        def verse(n: int) -> Section:
            def part(si: int) -> tuple:
                staff_map = maps.get(si, first)
                stacked = len(nums) > 1
                voice = min(staff_map.get(n, first.get(n, 0)), len(score.systems[si]) - 1) if stacked else 0
                voices = set(staff_map.values()) if stacked else {0}
                return (si, voice, tuple(filter(lambda k: k not in voices, range(len(score.systems[si])))))
            return Section("verse", n, tuple(map(part, sis)))
        return list(map(verse, nums))
    return list(chain.from_iterable(map(expand, blocks)))


def tail_pickup(score: Score, sections: list[Section]) -> tuple:
    """Verse pickup at the end of the response: notes outside the bar count (Sibelius special noteheads) or notes
    after the last rest of the final bar when the first verse bar is complete.
    Returns ((system, staff, measure), event indices, "extra" | "inbar") or ()."""
    resp = next(filter(lambda s: s.kind == "response", sections), None)
    first_verse = next(filter(lambda s: s.kind == "verse", sections), None)
    if resp is None or first_verse is None:
        return ()
    si, voice, _ = resp.parts[-1]
    measures = score.systems[si][voice].measures
    if not measures:
        return ()
    m, where = measures[-1], (si, voice, len(measures) - 1)
    extras = tuple(filter(lambda i: m.events[i].extra, range(len(m.events))))
    if extras:
        return (where, extras, "extra")
    rests = list(filter(lambda i: not m.events[i].heads, range(len(m.events))))
    if not rests or rests[-1] == len(m.events) - 1 or not any(map(lambda e: e.heads, m.events[:rests[-1]])):
        return ()
    trailing = tuple(range(rests[-1] + 1, len(m.events)))
    if sum(map(lambda i: m.events[i].value, trailing)) > m.expected / 2 + EPS:
        return ()
    vsi, vvoice, _ = first_verse.parts[0]
    vfirst = score.systems[vsi][vvoice].measures[0] if score.systems[vsi][vvoice].measures else None
    full_start = vfirst is not None and abs(vfirst.total - vfirst.expected) < EPS
    return (where, trailing, "inbar") if full_start else ()


def arrangement(score: Score) -> list[tuple]:
    """Playback order: R, V1, R, V2, ..., Vn, R. The response's verse pickup is silenced in the final response."""
    secs = sections_of(score)
    resp = next(filter(lambda s: s.kind == "response", secs), None)
    verses = sorted(filter(lambda s: s.kind == "verse", secs), key=lambda s: s.num)
    if resp is None or not verses:
        return list(map(lambda s: (s, False), secs))
    final = next(filter(lambda s: s.kind == "final", secs), None)
    middle = list(chain.from_iterable(map(lambda v: [(v, False), (resp, False)], verses)))
    return [(resp, False)] + middle[:-1] + ([(final, False)] if final else [(resp, True)])


def structure_report(score: Score) -> dict:
    secs = sections_of(score)
    pick = tail_pickup(score, secs)
    name = lambda s: ({"response": "R", "final": "Final"}.get(s.kind) or (f"V{s.num}" if s.kind == "verse" else "all")) + \
        "[" + ",".join(map(lambda p: f"s{p[0] + 1}" + (f".{p[1] + 1}" if p[1] else ""), s.parts)) + "]"
    order = " ".join(map(lambda sf: ("R*" if sf[1] else name(sf[0]).split("[")[0]), arrangement(score)))
    return {"sections": " ".join(map(name, secs)), "pickup_notes": len(pick[1]) if pick else 0,
            "pickup_kind": pick[2] if pick else None, "playback": order}

# ----------------------------------------------------------------------------- outputs
def playback_parts(score: Score, as_written: bool = False) -> list[tuple]:
    """(section index, system, voice staff, accompaniment staves, silence_pickup) in playback order."""
    plan = [(Section("score", 0, tuple(map(lambda si: (si, 0, tuple(range(1, len(score.systems[si])))), range(len(score.systems))))), False)] \
        if as_written else arrangement(score)
    return list(chain.from_iterable(map(lambda isf: map(lambda part: (isf[0], *part, isf[1][1]), isf[1][0].parts), enumerate(plan))))


def lane_notes(score: Score, as_written: bool = False) -> list[list[tuple]]:
    """Per lane: (start_beats, dur_beats, midi). Lane 0 follows the sung line through the arrangement; accompaniment
    lanes take the remaining staves counted from the bottom of each system. Ties merge within a section."""
    parts = playback_parts(score, as_written)
    pick = tail_pickup(score, sections_of(score))
    n_acc = max(map(lambda p: len(p[3]), parts)) if parts else 0
    def staff_events(si: int, k: int, silence: bool) -> list:
        measures = score.systems[si][k].measures
        if not (silence and pick and pick[0][:2] == (si, k)):
            return list(measures)
        mi, idx, kind = pick[0][2], set(pick[1]), pick[2]
        m = measures[mi]
        evs = tuple(filter(lambda ie: not (kind == "extra" and ie[0] in idx), enumerate(m.events)))
        evs = tuple(map(lambda ie: replace(ie[1], heads=(), tie=False) if ie[0] in idx else ie[1], evs))
        return list(measures[:mi]) + [replace(m, events=evs)] + list(measures[mi + 1:])
    def seg_len(p: tuple) -> float:
        sec, si, voice, accs, silence = p
        return max(map(lambda k: sum(map(lambda m: m.length, staff_events(si, k, silence and k == voice))), (voice,) + accs))
    starts = np.concatenate(([0.0], np.cumsum(list(map(seg_len, parts)))))
    def lane_staff(p: tuple, lane: int) -> int | None:
        sec, si, voice, accs, silence = p
        return voice if lane == 0 else (accs[-lane] if lane <= len(accs) else None)
    def lane(lane_i: int) -> list:
        def part_events(ip: tuple) -> list:
            i, p = ip
            k = lane_staff(p, lane_i)
            if k is None:
                return []
            evs = _with_offsets(tuple(staff_events(p[1], k, p[4] and k == p[2])), starts[i])
            boundary = i + 1 >= len(parts) or parts[i + 1][0] != p[0]
            return list(map(lambda te: (te[0], replace(te[1], tie=False) if boundary and te is evs[-1] else te[1], p[0]), evs))
        events = list(chain.from_iterable(map(part_events, enumerate(parts))))
        def step(acc: tuple, item: tuple) -> tuple:
            notes, open_ties = acc                   # open_ties: midi -> index of the note a tie continues
            t, e, _sec = item
            extend = set(e.midis) & set(open_ties)
            targets = set(map(lambda m: open_ties[m], extend))
            notes = list(map(lambda i_n: (i_n[1][0], i_n[1][1] + e.value, i_n[1][2]) if i_n[0] in targets else i_n[1], enumerate(notes)))
            fresh = list(map(lambda m: (t, e.value, m), filter(lambda m: m not in extend, e.midis)))
            base = len(notes)
            idx = {**dict(map(lambda m: (m, open_ties[m]), extend)), **dict(map(lambda j_m: (j_m[1][2], base + j_m[0]), enumerate(fresh)))}
            return notes + fresh, (idx if e.tie else {})
        return reduce(step, events, ([], {}))[0]
    return list(map(lane, range(1 + n_acc)))


def _with_offsets(measures: tuple, start: float) -> list:
    flat = list(chain.from_iterable(map(lambda m: m.events, measures)))
    offs = np.concatenate(([0.0], np.cumsum(list(map(lambda e: e.value, flat)))))[:-1] if flat else []
    return list(map(lambda oe: (start + oe[0], oe[1]), zip(offs, flat)))


def write_midi(score: Score, out: Path, tpq: int = 480, as_written: bool = False) -> Path:
    lanes = lane_notes(score, as_written)
    mid = mido.MidiFile(ticks_per_beat=tpq)
    first = score.systems[0][0].measures[0] if score.systems and score.systems[0][0].measures else None
    def track(k: int) -> mido.MidiTrack:
        tr = mido.MidiTrack()
        tr.append(mido.MetaMessage("track_name", name="Melody" if k == 0 else f"Accompaniment {k} (from bottom)", time=0))
        if k == 0:
            tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(score.tempo), time=0))
            if first:
                tr.append(mido.MetaMessage("time_signature", numerator=first.time[0], denominator=first.time[1], time=0))
        tr.append(mido.Message("program_change", channel=k % 16, program=0, time=0))
        evs = sorted(list(map(lambda n: (int(round(n[0] * tpq)), 1, n[2]), lanes[k])) +
                     list(map(lambda n: (int(round((n[0] + n[1]) * tpq)), 0, n[2]), lanes[k])))
        def emit(acc: tuple, ev: tuple) -> tuple:
            msgs, now = acc
            tick, on, m = ev
            msg = mido.Message("note_on" if on else "note_off", channel=k % 16, note=int(m), velocity=80 if on else 0, time=tick - now)
            return msgs + [msg], tick
        msgs, _ = reduce(emit, evs, ([], 0))
        list(map(tr.append, msgs))
        return tr
    list(map(lambda k: mid.tracks.append(track(k)), range(len(lanes))))
    out.parent.mkdir(parents=True, exist_ok=True)
    mid.save(out)
    return out


LILY_DUR = {8.0: "\\breve", 6.0: "1.", 4.0: "1", 3.0: "2.", 3.5: "2..", 2.0: "2", 1.5: "4.", 1.75: "4..", 1.0: "4",
            0.75: "8.", 0.875: "8..", 0.5: "8", 0.375: "16.", 0.25: "16", 0.125: "32"}


def lily_duration(v: float) -> str:
    near = next(filter(lambda k: abs(k - v) < 1e-4, LILY_DUR), None)
    return LILY_DUR[near] if near is not None else f"4*{Fraction(v).limit_denominator(48)}"


def lily_pitch(h: Head) -> str:
    shift = round((h.midi - diatonic_to_midi(h.d, 0)) / 12) * 12   # octave clefs move the sounding pitch
    alter = h.midi - shift - diatonic_to_midi(h.d, 0)
    name = "cdefgab"[h.d % 7] + ("is" * alter if alter > 0 else "es" * -alter)
    octv = h.d // 7 + shift // 12
    return name + ("'" * (octv - 3) if octv > 3 else "," * (3 - octv))


KEY_NAMES = {0: "c", 1: "g", 2: "d", 3: "a", 4: "e", 5: "b", 6: "fis", 7: "cis", -1: "f", -2: "bes", -3: "es", -4: "as", -5: "des", -6: "ges", -7: "ces"}
LILY_CLEF = {"G": "treble", "G8vb": "\"treble_8\"", "G8va": "\"treble^8\"", "F": "bass", "C": "alto"}


def lilypond_source(score: Score, lane: int = 0) -> str:
    def event(e: Event) -> str:
        dur = lily_duration(e.value)
        if not e.heads:
            return "r" + dur
        pitches = list(map(lily_pitch, sorted(e.heads, key=lambda h: h.midi)))
        body = pitches[0] if len(pitches) == 1 else "<" + " ".join(pitches) + ">"
        return body + dur + ("~" if e.tie else "")
    def measure(m: Measure, prev: Measure | None) -> str:
        head = (f"\\time {m.time[0]}/{m.time[1]} " if prev is None or prev.time != m.time else "") + \
               (f"\\key {KEY_NAMES.get(m.key, 'c')} \\major " if prev is None or prev.key != m.key else "") + \
               (f"\\clef {LILY_CLEF[m.clef]} " if prev is None or prev.clef != m.clef else "")
        flag = "" if abs(m.total - m.expected) < EPS else f" %{{ {m.total:g}/{m.expected:g} %}}"
        return head + " ".join(map(event, m.events)) + flag + " \\bar \"|\""
    ms = list(chain.from_iterable(map(lambda isys: map(lambda m: (m, isys[0]), isys[1][lane].measures),
                                      filter(lambda isys: lane < len(isys[1]), enumerate(score.systems)))))
    secs = sections_of(score)
    marks = dict(map(lambda sec: (sec.parts[0][0], {"response": "R", "final": "Final", "score": ""}.get(sec.kind, f"V{sec.num}")),
                     reversed(secs)))
    def render_m(i: int) -> str:
        m, si = ms[i]
        brk = " \\break\n" if i + 1 < len(ms) and ms[i + 1][1] != si else "\n"
        start = (i == 0 or ms[i - 1][1] != si) and marks.get(si)
        mark = f"\\mark \\markup \\box \"{marks[si]}\" " if start else ""
        return mark + measure(m, ms[i - 1][0] if i else None) + brk
    body = "".join(map(render_m, range(len(ms))))
    title = Path(score.path).stem.replace('"', "'")
    return ("\\version \"2.26.0\"\n\\header { title = \"" + title + "\" subtitle = \"vector_omr proof (lane " + str(lane + 1) + ")\" tagline = ##f }\n"
            "\\paper { #(set-paper-size \"a4\") indent = 0 }\n"
            "\\score { \\new Staff { \\cadenzaOn \\accidentalStyle modern\n" + body + "\\bar \"|.\" } \\layout { } }\n")


def write_proof(score: Score, out_dir: Path) -> Path | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(score.path).stem)
    ly = out_dir / f"{stem}.ly"
    ly.write_text(lilypond_source(score))
    res = subprocess.run(["lilypond", "-dno-point-and-click", "-o", str(out_dir / stem), str(ly)], capture_output=True, text=True)
    return out_dir / f"{stem}.pdf" if res.returncode == 0 else None


def convert(pdf: Path, out_dir: Path, proof_dir: Path | None, as_written: bool = False) -> dict:
    score = read_score(pdf)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", pdf.stem)
    mid = write_midi(score, out_dir / f"{stem}.mid", as_written=as_written)
    proof = write_proof(score, proof_dir) if proof_dir else None
    return {"pdf": pdf.name, "midi": str(mid), "proof": str(proof) if proof else None, "tempo_qpm": score.tempo, **score.report}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("convert")
    c.add_argument("pdfs", nargs="+", type=Path)
    c.add_argument("--out", type=Path, default=Path("digitized_scores/vector_midi"))
    c.add_argument("--proof", type=Path, default=None)
    c.add_argument("--report", type=Path, default=None)
    c.add_argument("--as-written", action="store_true", help="play the page top to bottom once (no response/verse arrangement)")
    a = ap.parse_args(argv[1:])
    def safe(p: Path) -> dict:
        try:
            return convert(p, a.out, a.proof, a.as_written)
        except Exception as exc:  # report and continue with the batch
            return {"pdf": p.name, "error": f"{type(exc).__name__}: {exc}"}
    results = list(map(safe, a.pdfs))
    line = lambda r: f"{r['pdf'][:48]:48s} ERROR {r['error']}" if "error" in r else (f"{r['pdf'][:48]:48s} sys={r['systems']:2d} staves={r['staves']:2d} bars={r['measures']:3d} notes={r['notes']:3d} "
                      f"key={r['key']:+d} time={r['time']} q={r['tempo_qpm']:g} full={r['full']} edge-short={len(r['under']) - len(r['suspect']) + len(r['over'])} suspect={len(r['suspect'])}"
                      f"\n{'':48s} play: {r['playback']}  pickup={r['pickup_notes']}")
    print("\n".join(map(line, results)))
    if a.report:
        a.report.write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

# <!-- APAF Bioinformatics | vector_omr.py | Approved | 2026-10-25 -->
