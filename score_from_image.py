#!/usr/bin/env python
"""Photo or scan of a printed score -> engraved PDF, MIDI and LilyPond source, in one command.

Pipeline of `convert`:
  1. homr        reads notes, rests, clefs, keys, metres, ties and slurs, and straightens every staff.
  2. Audiveris   (optional) reads markings from the straightened staves (dynamics, hairpins, bowings,
                 fermatas, accents, fingerings); each is attached to the homr note it aligns with.
  3. Claude      (optional, --refine claude) compares every straightened staff with the draft and corrects
                 notes and markings; title, composer and tempo are read from the page.
  4. Validation  every bar is summed against the metre; failures go to report.json and the review PDF.
  5. LilyPond    engraves the score with the photo's line breaks and writes MIDI. The review PDF puts each
                 photo staff above its engraving, with suspect bars marked, for proof-reading.

Interpreter: the `omr` conda env (homr, music21, anthropic, scikit-image):
    /Users/ignatiuspang/anaconda3/envs/omr/bin/python score_from_image.py convert photo.jpg --out digitized_scores/from_image
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import difflib
import io
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from fractions import Fraction
from functools import reduce
from itertools import accumulate, chain, groupby, product
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

MODEL = "claude-opus-5-5"
PRICE_PER_MTOK = (4.0, 20.0)                     # USD input / output for MODEL
AUDIVERIS_CANDIDATES = (
    str(Path.home() / "Applications/Audiveris.app/Contents/MacOS/Audiveris"),
    "/Applications/Audiveris.app/Contents/MacOS/Audiveris",
)

# ---------------------------------------------------------------- pitches and durations

ALTER_NAME = {-2: "eses", -1: "es", 0: "", 1: "is", 2: "isis"}
NAME_ALTER = {"isis": 2, "is": 1, "": 0, "es": -1, "s": -1, "eses": -2}
PITCH_RE = re.compile(r"^([a-g])(isis|eses|is|es|s)?([',]*)$")
STEP_SEMI = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
BASE = {Fraction(8): "\\breve", Fraction(4): "1", Fraction(2): "2", Fraction(1): "4", Fraction(1, 2): "8",
        Fraction(1, 4): "16", Fraction(1, 8): "32", Fraction(1, 16): "64", Fraction(1, 32): "128"}
DUR_RE = re.compile(r"^(\\breve|1|2|4|8|16|32|64|128)(\.*)(?:\*(\d+)(?:/(\d+))?)?$")


def lily_pitch(step: str, alter: int, octave: int) -> str:
    """LilyPond absolute pitch (Dutch names): c' is middle C."""
    marks = "'" * (octave - 3) if octave >= 3 else "," * (3 - octave)
    return step.lower() + ALTER_NAME[alter] + marks


def pitch_midi(name: str) -> int:
    step, acc, octs = PITCH_RE.match(name).groups()
    return 12 * (4 + octs.count("'") - octs.count(",")) + STEP_SEMI[step] + NAME_ALTER[acc or ""]


def lily_duration(q: Fraction) -> str:
    """Quarter-note length -> LilyPond duration; non-dyadic lengths become scaled durations (8*2/3)."""
    dotted = filter(lambda bd: bd[0] * (2 - Fraction(1, 2 ** bd[1])) == q, product(BASE, range(3)))
    hit = next(dotted, None)
    if hit:
        return BASE[hit[0]] + "." * hit[1]
    base = min(filter(lambda b: b >= q, BASE), default=Fraction(8))
    r = q / base
    return f"{BASE[base]}*{r.numerator}/{r.denominator}"


def parse_duration(s: str) -> Fraction:
    m = DUR_RE.match(s.strip())
    if not m:
        raise ValueError(f"bad duration {s!r}")
    base = Fraction(8) if m[1] == "\\breve" else Fraction(4, int(m[1]))
    return base * (2 - Fraction(1, 2 ** len(m[2]))) * Fraction(int(m[3] or 1), int(m[4] or 1))


# ---------------------------------------------------------------- marks vocabulary

MARK_OF_CLASS = {
    "DownBow": "\\downbow", "UpBow": "\\upbow", "Staccato": "-.", "Staccatissimo": "-!", "Accent": "->",
    "StrongAccent": "-^", "Tenuto": "--", "DetachedLegato": "-_", "Harmonic": "\\flageolet", "Stopped": "-+",
    "OpenString": "\\open", "SnapPizzicato": "\\snappizzicato", "BreathMark": "\\breathe", "Caesura": "\\caesura",
    "Fermata": "\\fermata", "Trill": "\\trill", "Mordent": "\\mordent", "InvertedMordent": "\\prall",
    "Turn": "\\turn", "InvertedTurn": "\\reverseturn", "ArpeggioMark": "\\arpeggio",
}
DYNAMICS = ("ppppp", "pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "ffff", "fffff",
            "fp", "sf", "sff", "sp", "spp", "sfz", "sfp", "rfz", "fz", "n")
SPANS = ("(", ")", "\\<", "\\>", "\\!")
AFTER = ("\\breathe", "\\caesura")               # standalone events written after their note
FIXED_MARKS = frozenset(chain(MARK_OF_CLASS.values(), SPANS, map(lambda d: "\\" + d, DYNAMICS)))
FINGER_RE = re.compile(r"^-[0-5]$")
TEXT_RE = re.compile(r'^text(_below)?:[^"\\]{1,60}$')
CHANGE_RE = re.compile(r'^\\(clef "?[a-z_0-9^]+"?|key [a-g](is|es|s)? \\(major|minor)|time \d+/\d+)$')
MARK_GROUPS = {
    "bowing": ("\\downbow", "\\upbow"), "dynamics": tuple(map(lambda d: "\\" + d, DYNAMICS)),
    "hairpins": ("\\<", "\\>", "\\!"), "fermata": ("\\fermata",), "accent": ("->", "-^"),
    "tenuto": ("--", "-_"), "staccato": ("-.", "-!"), "slur": ("(", ")"), "breath": AFTER,
    "ornament": ("\\trill", "\\mordent", "\\prall", "\\turn", "\\reverseturn"),
}
DEFAULT_AUDIVERIS_GROUPS = "bowing,dynamics,hairpins"   # measured precise on photos; others opt-in
HOMR_DOUBTFUL = ("\\trill", "\\breathe")         # homr emits these spuriously on photos


def valid_mark(m: str) -> bool:
    return m in FIXED_MARKS or bool(FINGER_RE.match(m) or TEXT_RE.match(m))


def mark_group(m: str) -> str:
    named = next(filter(lambda kv: m in kv[1], MARK_GROUPS.items()), None)
    return named[0] if named else "fingering" if FINGER_RE.match(m) else "text" if TEXT_RE.match(m) else "other"


def mark_text(m: str) -> str:
    if m.startswith("text"):
        side, words = m.split(":", 1)
        return ("_" if side == "text_below" else "^") + f'\\markup \\italic "{words}"'
    return m


# ---------------------------------------------------------------- score model

@dataclass(frozen=True)
class Ev:
    pitches: tuple[str, ...]            # LilyPond absolute pitches; empty means rest
    dur: Fraction                       # in quarter notes
    tie: bool = False
    grace: bool = False
    marks: tuple[str, ...] = ()

    @property
    def key(self) -> tuple:
        return tuple(map(pitch_midi, self.pitches)) or ("r",)


@dataclass(frozen=True)
class Bar:
    events: tuple[Ev, ...]
    changes: tuple[str, ...] = ()       # \clef, \key, \time at the start of the bar

    @property
    def length(self) -> Fraction:
        return sum(map(lambda e: e.dur, filter(lambda e: not e.grace, self.events)), Fraction(0))


@dataclass(frozen=True)
class Part:
    clef: str
    bars: tuple[Bar, ...]


@dataclass(frozen=True)
class Score:
    parts: tuple[Part, ...]
    breaks: tuple[int, ...]             # first bar index of every system
    key: tuple[int, str] = (0, "major")
    time: tuple[int, int] = (4, 4)
    time_symbol: str = "numeric"
    title: str = ""
    subtitle: str = ""
    composer: str = ""
    arranger: str = ""
    tempo_text: str = ""
    tempo: tuple[str, int] | None = None    # (beat duration, bpm)

    def system_ranges(self) -> list[tuple[int, int]]:
        ends = self.breaks[1:] + (len(self.parts[0].bars),)
        return list(zip(self.breaks, ends))


MAJOR = ("ces", "ges", "des", "aes", "ees", "bes", "f", "c", "g", "d", "a", "e", "b", "fis", "cis")
MINOR = ("aes", "ees", "bes", "f", "c", "g", "d", "a", "e", "b", "fis", "cis", "gis", "dis", "ais")
CLEF = {"TrebleClef": "treble", "GClef": "treble", "Treble8vbClef": '"treble_8"', "Treble8vaClef": '"treble^8"',
        "BassClef": "bass", "FClef": "bass", "Bass8vbClef": '"bass_8"', "AltoClef": "alto", "CClef": "alto",
        "TenorClef": "tenor", "SopranoClef": "soprano", "MezzoSopranoClef": "mezzosoprano",
        "BaritoneClef": "baritone", "PercussionClef": "percussion"}


def key_token(fifths: int, mode: str) -> str:
    return f"\\key {(MINOR if mode == 'minor' else MAJOR)[max(-7, min(7, fifths)) + 7]} \\{mode}"


def bar_expected(score: Score, part: int) -> list[Fraction]:
    """Metre length of every bar, following \\time changes."""
    def step(cur: Fraction, bar: Bar) -> Fraction:
        times = list(filter(lambda c: c.startswith("\\time"), bar.changes))
        if not times:
            return cur
        n, d = map(int, times[-1].split()[1].split("/"))
        return Fraction(4 * n, d)
    first = Fraction(4 * score.time[0], score.time[1])
    return list(accumulate(score.parts[part].bars, step, initial=first))[1:]


def bar_check(score: Score) -> list[dict]:
    """Bars whose notes do not add up to the metre. A short first bar is a pickup, a short last bar a closing bar."""
    def part_rows(pi: int) -> list[dict]:
        bars, expected = score.parts[pi].bars, bar_expected(score, pi)
        last = len(bars) - 1
        def row(i: int) -> dict | None:
            got, exp = bars[i].length, expected[i]
            if got == exp:
                return None
            kind = ("over" if got > exp else "pickup" if i == 0 else "closing" if i == last else "short")
            system = sum(map(lambda b: b <= i, score.breaks))
            return {"part": pi + 1, "bar": i + 1, "system": system, "got": str(got), "expected": str(exp), "kind": kind}
        return list(filter(None, map(row, range(len(bars)))))
    return list(chain.from_iterable(map(part_rows, range(len(score.parts)))))


def suspect_bars(rows: list[dict]) -> list[dict]:
    return list(filter(lambda r: r["kind"] in ("over", "short"), rows))


# ---------------------------------------------------------------- MusicXML -> model

def from_musicxml(path: Path, keep_doubtful: bool = True) -> Score:
    import music21 as m21
    s = m21.converter.parse(str(path))
    parts = list(s.parts) if s.parts else [s]
    span_kind = {"Slur": ("(", ")"), "Crescendo": ("\\<", "\\!"), "Diminuendo": ("\\>", "\\!")}

    def span_pairs(sp) -> list[tuple[int, str]]:
        kind, first, last = span_kind.get(type(sp).__name__), sp.getFirst(), sp.getLast()
        return [] if kind is None or first is None or first is last else [(id(first), kind[0]), (id(last), kind[1])]

    spanned = reduce(lambda d, kv: {**d, kv[0]: d.get(kv[0], ()) + (kv[1],)},
                     chain.from_iterable(map(span_pairs, s.spannerBundle)), {})

    def direction_mark(el) -> str | None:
        if type(el).__name__ == "Dynamic":
            v = str(el.value)
            return "\\" + v if v in DYNAMICS else f"text_below:{v}"
        words = re.sub(r'["\\]', "", str(getattr(el, "content", "") or "")).strip()[:60]
        return (("text_below:" if getattr(el, "placement", None) == "below" else "text:") + words) if words else None

    def ev_of(n, extra: tuple[str, ...]) -> Ev:
        pitches = () if n.isRest else tuple(map(lambda p: lily_pitch(p.step, int(p.alter or 0), p.octave), n.pitches))
        grace = n.duration.isGrace
        q = m21.duration.Duration(n.duration.type).quarterLength if grace else n.quarterLength
        finger = lambda a: f"-{a.fingerNumber}" if str(a.fingerNumber).isdigit() and int(a.fingerNumber) <= 5 else None
        art = map(lambda a: finger(a) if type(a).__name__ == "Fingering" else MARK_OF_CLASS.get(type(a).__name__),
                  n.articulations)
        expr = map(lambda x: MARK_OF_CLASS.get(type(x).__name__), n.expressions)
        marks = tuple(filter(None, chain(art, expr, spanned.get(id(n), ()), extra)))
        marks = marks if keep_doubtful else tuple(filter(lambda m: m not in HOMR_DOUBTFUL, marks))
        tie = n.tie is not None and n.tie.type in ("start", "continue") and not n.isRest
        return Ev(pitches, Fraction(q).limit_denominator(96), tie, grace, tuple(dict.fromkeys(marks)))

    def bar_of(m, changes: tuple[str, ...]) -> Bar:
        src = m.voices[0] if m.voices else m
        notes = list(src.notesAndRests)
        offs = list(map(lambda n: float(n.getOffsetInHierarchy(m)), notes))
        dirs = list(m.recurse().getElementsByClass(("Dynamic", "TextExpression")))

        def target(el) -> int:
            off = float(el.getOffsetInHierarchy(m))
            return next(filter(lambda i: offs[i] >= off - 1e-6, range(len(notes))), len(notes) - 1)

        attached = reduce(lambda d, el: {**d, target(el): d.get(target(el), ()) + (direction_mark(el),)},
                          filter(lambda el: notes and direction_mark(el), dirs), {})
        return Bar(tuple(map(lambda i: ev_of(notes[i], tuple(filter(None, attached.get(i, ())))), range(len(notes)))),
                   changes)

    def part_of(p) -> tuple[Part, list]:
        measures = list(p.getElementsByClass("Measure"))
        first = measures[0]
        clef0 = CLEF.get(type(first.clef).__name__, "treble") if first.clef else "treble"

        def step(acc: tuple, m) -> tuple:
            bars, state = acc
            now = {"clef": f"\\clef {CLEF.get(type(m.clef).__name__, 'treble')}" if m.clef else state["clef"],
                   "key": key_token(m.keySignature.sharps, getattr(m.keySignature, "mode", "major") or "major")
                   if m.keySignature else state["key"],
                   "time": f"\\time {m.timeSignature.ratioString}" if m.timeSignature else state["time"]}
            changes = tuple(filter(None, map(lambda k: now[k] if bars and now[k] != state[k] else None,
                                             ("clef", "key", "time"))))
            return bars + [bar_of(m, changes)], now

        start = {"clef": f"\\clef {clef0}", "key": None, "time": None}
        bars, _ = reduce(step, measures, ([], start))
        return Part(clef0, tuple(bars)), measures

    built = list(map(part_of, parts))
    measures0 = built[0][1]
    first = measures0[0]
    new_system = lambda m: any(map(lambda lay: getattr(lay, "isNew", False), m.getElementsByClass("SystemLayout")))
    breaks = tuple(sorted(set([0]) | set(filter(lambda i: new_system(measures0[i]), range(len(measures0))))))
    ks, ts = first.keySignature, first.timeSignature
    mode = (getattr(ks, "mode", "major") or "major") if ks else "major"
    tempo_mark = next(iter(s.recurse().getElementsByClass("MetronomeMark")), None)
    tempo = ((lily_duration(Fraction(tempo_mark.referent.quarterLength)), int(tempo_mark.number))
             if tempo_mark is not None and tempo_mark.number else None)
    return Score(parts=tuple(map(lambda b: b[0], built)), breaks=breaks,
                 key=(ks.sharps if ks else 0, mode if mode in ("major", "minor") else "major"),
                 time=(ts.numerator, ts.denominator) if ts else (4, 4),
                 time_symbol={"common": "common", "cut": "cut"}.get(getattr(ts, "symbol", ""), "numeric"),
                 tempo=tempo)


def concat_scores(scores: list[Score]) -> Score:
    """Join page scores into one (same parts on every page)."""
    def join(a: Score, b: Score) -> Score:
        n = len(a.parts[0].bars)
        parts = tuple(map(lambda pq: Part(pq[0].clef, pq[0].bars + pq[1].bars), zip(a.parts, b.parts)))
        return replace(a, parts=parts, breaks=a.breaks + tuple(map(lambda x: x + n, b.breaks)))
    return reduce(join, scores)


# ---------------------------------------------------------------- spanner hygiene

def fix_pairs(part: Part, opens: tuple[str, ...], close: str, restart_ok: bool) -> Part:
    """Drop closing marks with no opener and openers never closed, so LilyPond draws no runaway slurs or hairpins."""
    flat = list(chain.from_iterable(map(lambda bi: map(lambda ei: (bi, ei), range(len(part.bars[bi].events))),
                                        range(len(part.bars)))))
    ev = lambda be: part.bars[be[0]].events[be[1]]

    def step(acc: tuple, be: tuple) -> tuple:
        open_at, drops = acc
        marks = ev(be).marks
        closes = close in marks
        drops = drops | ({(be, close)} if closes and open_at is None else set())
        open_at = None if closes else open_at
        starts = next(filter(lambda m: m in opens, marks), None)
        if starts and open_at is not None and not restart_ok:
            return open_at, drops | {(be, starts)}
        return (be, starts) if starts else open_at, drops

    open_at, drops = reduce(step, flat, (None, set()))
    drops = drops | ({open_at} if open_at else set())

    def clean(bi: int) -> Bar:
        bar = part.bars[bi]
        evs = tuple(map(lambda ei: replace(bar.events[ei], marks=tuple(filter(
            lambda m: ((bi, ei), m) not in drops, bar.events[ei].marks))), range(len(bar.events))))
        return replace(bar, events=evs)

    return replace(part, bars=tuple(map(clean, range(len(part.bars)))))


def tidy(score: Score) -> Score:
    fix = lambda p: fix_pairs(fix_pairs(p, ("(",), ")", False), ("\\<", "\\>"), "\\!", True)
    return replace(score, parts=tuple(map(fix, score.parts)))


# ---------------------------------------------------------------- model -> LilyPond

def ev_text(e: Ev, scale: Fraction = Fraction(1)) -> str:
    order = lambda m: 0 if m == ")" else 2 if m == "(" else 1
    body = ("<" + " ".join(e.pitches) + ">" if len(e.pitches) > 1 else e.pitches[0]) if e.pitches else "r"
    core = body + lily_duration(e.dur * scale) + ("~" if e.tie and e.pitches else "")
    post = "".join(map(mark_text, sorted(filter(lambda m: m not in AFTER, e.marks), key=order)))
    after = "".join(map(lambda m: " " + m, filter(lambda m: m in AFTER, e.marks)))
    return ("\\grace " if e.grace else "") + core + post + after


def triplet_like(e: Ev) -> bool:
    return not e.grace and e.dur.denominator % 3 == 0


def events_text(events: tuple[Ev, ...]) -> str:
    """Runs of triplet-valued notes are written as \\tuplet 3/2 groups."""
    def chunk(run: list[Ev]) -> list[list[Ev]]:
        def step(acc: list, e: Ev) -> list:
            cur = acc[-1] + [e]
            closed = sum(map(lambda x: x.dur, cur), Fraction(0)).denominator % 3 != 0
            return acc[:-1] + [cur] + ([[]] if closed else [])
        return list(filter(None, reduce(step, run, [[]])))

    def group_text(g: list[Ev]) -> str:
        whole = sum(map(lambda x: x.dur, g), Fraction(0)).denominator % 3 != 0
        return ("\\tuplet 3/2 { " + " ".join(map(lambda x: ev_text(x, Fraction(3, 2)), g)) + " }" if whole
                else " ".join(map(ev_text, g)))

    runs = groupby(events, key=triplet_like)
    return " ".join(map(lambda kv: " ".join(map(group_text, chunk(list(kv[1])))) if kv[0]
                        else " ".join(map(ev_text, kv[1])), runs))


def _prelude_at(score: Score, part: int, start: int) -> list[str]:
    """Clef, key and time in force at bar `start`."""
    initial = {"clef": f"\\clef {score.parts[part].clef}", "key": key_token(*score.key),
               "time": f"\\time {score.time[0]}/{score.time[1]}"}
    kind = lambda c: c.split()[0][1:]
    state = reduce(lambda st, c: {**st, kind(c): c}, chain.from_iterable(
        map(lambda b: b.changes, score.parts[part].bars[:start])), initial)
    return [state["clef"], state["key"], state["time"]]


def _esc(s: str) -> str:
    return s.replace("\\", "").replace('"', "'")


def part_music(score: Score, part: int, systems: tuple[int, ...], review: bool, suspects: set) -> str:
    ranges = score.system_ranges()
    expected = bar_expected(score, part)
    bars = score.parts[part].bars
    first_bar = ranges[systems[0]][0]
    head = _prelude_at(score, part, first_bar)
    symbol = {"common": "\\defaultTimeSignature", "cut": "\\defaultTimeSignature"}.get(score.time_symbol,
                                                                                         "\\numericTimeSignature")
    tempo = ""
    if part == 0 and first_bar == 0 and (score.tempo_text or score.tempo):
        words = f'"{_esc(score.tempo_text)}" ' if score.tempo_text else ""
        tempo = f"\\tempo {words}{score.tempo[0]} = {score.tempo[1]}" if score.tempo else f"\\tempo {words}".strip()
    pickup = (f"\\partial {lily_duration(bars[0].length)}"
              if first_bar == 0 and Fraction(0) < bars[0].length < expected[0] else "")

    def bar_line(i: int) -> str:
        bar, exp = bars[i], expected[i]
        odd = bar.length != exp and not (i == 0 and pickup) and bar.length > 0
        set_len = f"\\set Timing.measureLength = #{bar.length / 4} " if odd else ""
        reset = f" \\set Timing.measureLength = #{exp / 4}" if odd else ""
        flag = '<>^\\markup \\with-color #red \\bold "?" ' if review and (part + 1, i + 1) in suspects else ""
        text = events_text(bar.events) or f"s{lily_duration(exp)}"
        return "  " + " ".join(filter(None, [*bar.changes, set_len + flag + text + " |" + reset])) + f"  % bar {i + 1}"

    def system_block(k: int) -> str:
        a, b = ranges[k]
        lines = list(map(bar_line, range(a, b)))
        brk = "  \\break" if not review and k != systems[-1] else ""
        return f"  % system {k + 1}\n" + "\n".join(lines) + ("\n" + brk if brk else "")

    number = f"\\set Score.currentBarNumber = #{first_bar + 1}" if first_bar else ""
    final = '\n  \\bar "|."' if systems[-1] == len(ranges) - 1 and not review else ""
    opening = " ".join(filter(None, [symbol, *head, tempo, number, pickup]))
    return "{\n  " + opening + "\n" + "\n".join(map(system_block, systems)) + final + "\n}"


def lilypond_source(score: Score, systems: tuple[int, ...] | None = None, review: bool = False,
                    instrument: str = "acoustic grand", suspects: set = frozenset()) -> str:
    systems = systems if systems is not None else tuple(range(len(score.breaks)))
    music = list(map(lambda p: part_music(score, p, systems, review, suspects), range(len(score.parts))))
    staff = lambda i: f'\\new Staff \\with {{ midiInstrument = "{instrument}" }} {music[i]}'
    staves = list(map(staff, range(len(music))))
    group = (staves[0] if len(staves) == 1 else
             "\\new PianoStaff <<\n" + "\n".join(staves) + "\n>>" if len(staves) == 2 else
             "\\new StaffGroup <<\n" + "\n".join(staves) + "\n>>")
    header = "" if review else "\\header {\n" + "".join(map(
        lambda kv: f'  {kv[0]} = "{_esc(kv[1])}"\n', filter(lambda kv: kv[1], (
            ("title", score.title), ("subtitle", score.subtitle), ("composer", score.composer),
            ("arranger", score.arranger))))) + "  tagline = ##f\n}\n"
    numbers = ("\\override BarNumber.break-visibility = ##(#f #t #t)\n    "
               "barNumberVisibility = #all-bar-numbers-visible" if review else "")
    layout = ("\\layout {\n  \\context { \\Score\n    \\override NonMusicalPaperColumn.line-break-permission = ##f\n"
              f"    {numbers}\n  }}\n}}")
    paper = ("\\paper { indent = 0 tagline = ##f line-width = 190\\mm ragged-right = ##f }" if review else
             '\\paper {\n  #(set-paper-size "a4")\n  indent = 0\n  ragged-last = ##f\n'
             '  system-system-spacing.basic-distance = #16\n}')
    midi = "" if review else (f"\\score {{\n{group}\n\\midi {{ }}\n}}\n" if score.tempo else
                              f"\\score {{\n{group}\n\\midi {{ \\tempo 4 = 90 }}\n}}\n")
    return (f'\\version "2.24.0"\n% <!-- APAF Bioinformatics | score_from_image.py output | Approved -->\n'
            f"{header}{paper}\n\\score {{\n{group}\n{layout}\n}}\n{midi}")


def run_lilypond(ly: Path, out_stem: Path, extra: tuple[str, ...] = ()) -> str:
    r = subprocess.run(["lilypond", "-dno-point-and-click", *extra, "-o", str(out_stem), str(ly)],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError("LilyPond failed:\n" + r.stderr[-3000:])
    return r.stderr


# ---------------------------------------------------------------- homr (notes + straightened staves)

def run_homr(image: Path, work: Path) -> tuple[Path, dict[int, Image.Image]]:
    """Run homr in-process and keep the dewarped staff images it builds."""
    import homr.main as hm
    import homr.staff_parsing as sp
    from homr.onnx_providers import coreml_available
    work.mkdir(parents=True, exist_ok=True)
    local = work / image.name
    shutil.copy(image, local)
    captured: dict[int, Image.Image] = {}
    original = sp.prepare_staff_image

    def spy(debug, index, staff, staff_image, regions):
        img, st = original(debug, index, staff, staff_image, regions)
        arr = np.asarray(img)
        captured[index] = Image.fromarray(arr[..., ::-1] if arr.ndim == 3 else arr).convert("L")
        return img, st

    sp.prepare_staff_image = spy
    gpu = coreml_available()
    try:
        with open(work / "homr.log", "w") as log, contextlib.redirect_stderr(log):
            hm.download_weights(gpu, False, False)
            hm.process_image(str(local), hm.ProcessingConfig(False, False, False, False, -1, False, gpu, False),
                             hm.XmlGeneratorArguments(False, None, None))
    finally:
        sp.prepare_staff_image = original
    list(map(lambda kv: kv[1].save(work / f"{local.stem}_staff{kv[0]:02d}.png"), captured.items()))
    return local.with_suffix(".musicxml"), captured


def strips_by_system(captured: dict[int, Image.Image], n_systems: int, n_parts: int) -> list[list[Image.Image]] | None:
    """homr numbers staves voice by voice: index = part * systems + system."""
    if len(captured) != n_systems * n_parts:
        return None
    return list(map(lambda s: list(map(lambda p: captured[p * n_systems + s], range(n_parts))), range(n_systems)))


# ---------------------------------------------------------------- Audiveris (markings)

def find_audiveris(explicit: str | None) -> str | None:
    cands = (explicit or "", os.environ.get("AUDIVERIS", ""), *AUDIVERIS_CANDIDATES)
    return next(filter(lambda p: p and Path(p).exists(), cands), None)


def flat_page(strips: list[Image.Image]) -> Image.Image:
    """Stack straightened staves into one flat, binarised page at about 22 px staff spacing.
    Pixels must be both locally dark and globally dark, which drops most grey pencil."""
    from skimage.filters import threshold_local, threshold_otsu
    big = list(map(lambda im: np.asarray(im.resize((im.width * 2, im.height * 2), Image.LANCZOS), float), strips))
    ink = list(map(lambda a: (a < threshold_local(a, 101, offset=12)) & (a < threshold_otsu(a)), big))
    return Image.fromarray(np.where(np.vstack(ink), 0, 255).astype(np.uint8))


def run_audiveris(exe: str, page: Path, out_dir: Path) -> list[Path]:
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    subprocess.run([exe, "-batch", "-export", "-output", str(out_dir), "--", str(page)],
                   capture_output=True, text=True, timeout=900)
    movement = lambda p: int(re.search(r"mvt(\d+)", p.name)[1]) if "mvt" in p.name else 0
    return sorted(out_dir.glob("*.mxl"), key=movement)


def merge_marks(base: Score, other: Score, part: int, groups: set[str]) -> tuple[Score, int]:
    """Copy markings from `other` onto the base notes they align with (same pitch, in order)."""
    def flat(p: Part) -> list[tuple[int, int, Ev]]:
        return list(chain.from_iterable(map(lambda bi: map(lambda ei: (bi, ei, p.bars[bi].events[ei]),
                                                            range(len(p.bars[bi].events))), range(len(p.bars)))))
    a = list(filter(lambda t: not t[2].grace, flat(base.parts[part])))
    b = list(filter(lambda t: not t[2].grace, chain.from_iterable(map(lambda pp: flat(pp), other.parts[:1]))))
    sm = difflib.SequenceMatcher(a=list(map(lambda t: t[2].key, a)), b=list(map(lambda t: t[2].key, b)), autojunk=False)
    pairs = chain.from_iterable(map(lambda blk: zip(range(blk.a, blk.a + blk.size), range(blk.b, blk.b + blk.size)),
                                    sm.get_matching_blocks()))
    wanted = lambda m: mark_group(m) in groups
    adds = dict(filter(lambda kv: kv[1], map(lambda ij: ((a[ij[0]][0], a[ij[0]][1]), tuple(filter(
        lambda m: wanted(m) and m not in a[ij[0]][2].marks, b[ij[1]][2].marks))), pairs)))
    p = base.parts[part]
    bars = tuple(map(lambda bi: replace(p.bars[bi], events=tuple(map(
        lambda ei: replace(p.bars[bi].events[ei], marks=p.bars[bi].events[ei].marks + adds.get((bi, ei), ())),
        range(len(p.bars[bi].events))))), range(len(p.bars))))
    parts = base.parts[:part] + (replace(p, bars=bars),) + base.parts[part + 1:]
    return replace(base, parts=parts), sum(map(len, adds.values()))


def audiveris_pass(score: Score, systems: list[list[Image.Image]], exe: str, work: Path,
                   groups: set[str]) -> tuple[Score, dict]:
    def one(acc: tuple, part: int) -> tuple:
        sc, log = acc
        page = work / f"audiveris_part{part + 1}.png"
        flat_page(list(map(lambda s: s[part], systems))).save(page, dpi=(300, 300))
        mxls = run_audiveris(exe, page, work / f"audiveris_part{part + 1}")
        if not mxls:
            return sc, log + [{"part": part + 1, "status": "Audiveris produced no MusicXML"}]
        other = concat_scores(list(map(from_musicxml, mxls)))
        merged, n = merge_marks(sc, other, part, groups)
        return merged, log + [{"part": part + 1, "status": "ok", "marks_added": n, "movements": len(mxls)}]
    sc, log = reduce(one, range(len(score.parts)), (score, []))
    return sc, {"parts": log, "groups": sorted(groups)}


# ---------------------------------------------------------------- Claude refinement

EVENT_SCHEMA = {"type": "object", "additionalProperties": False,
                "required": ["pitches", "duration", "tie", "grace", "marks"],
                "properties": {"pitches": {"type": "array", "items": {"type": "string"}},
                               "duration": {"type": "string"}, "tie": {"type": "boolean"},
                               "grace": {"type": "boolean"}, "marks": {"type": "array", "items": {"type": "string"}}}}
BAR_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["changes", "events"],
              "properties": {"changes": {"type": "array", "items": {"type": "string"}},
                             "events": {"type": "array", "items": EVENT_SCHEMA}}}
SYSTEM_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["parts", "notes"],
                 "properties": {"parts": {"type": "array", "items": {
                     "type": "object", "additionalProperties": False, "required": ["bars"],
                     "properties": {"bars": {"type": "array", "items": BAR_SCHEMA}}}},
                     "notes": {"type": "string"}}}
HEADER_SCHEMA = {"type": "object", "additionalProperties": False,
                 "required": ["title", "subtitle", "composer", "arranger", "tempo_text", "tempo_beat", "tempo_bpm",
                              "time_symbol"],
                 "properties": {"title": {"type": "string"}, "subtitle": {"type": "string"},
                                "composer": {"type": "string"}, "arranger": {"type": "string"},
                                "tempo_text": {"type": "string"}, "tempo_beat": {"type": "string"},
                                "tempo_bpm": {"type": "integer"},
                                "time_symbol": {"type": "string", "enum": ["numeric", "common", "cut"]}}}

REFINE_PROMPT = f"""You proof-read optical music recognition (OMR) output against a photo of a printed score.
You receive one system (one line of music) as a straightened image, split into a left and right half that overlap,
plus the OMR draft of that system as JSON. Return the corrected system in the same JSON form so that it matches
the PRINTED music exactly.

Rules:
- Transcribe only printed engraving. Ignore handwriting and pencil: circles, crosses, written words, hand-drawn
  hairpins, pencilled fingerings or bowings. Printed and handwritten fingerings differ: printed digits are crisp
  and uniform in size.
- Keep one JSON bar per printed bar line. Fix bars the OMR merged or split.
- pitches: LilyPond absolute Dutch names. c' = middle C (C4), c'' = C5, b = B3, g, = G2. Sharp = "is", flat = "es"
  (fis'' = F#5, bes = Bb3, ees' = Eb4). Write the SOUNDING pitch: apply the key signature and any accidental
  earlier in the same bar. Empty list = rest. Several pitches = chord.
- duration: "1" whole, "2" half, "4" quarter, "8", "16", "32", dots appended ("4.", "8.."). Triplet notes take
  the scaled form: a triplet eighth is "8*2/3", a triplet quarter "4*2/3". Bar durations must add up to the metre,
  except a pickup in the very first bar and the closing bar of the piece.
- tie: true when the note is tied to the next note. grace: true for grace notes.
- marks, attached to the note they belong to, from this list only:
  slurs "(" on the first note and ")" on the last note; hairpins "\\\\<" or "\\\\>" on the first note and "\\\\!" on
  the note where it ends; dynamics {", ".join(map(lambda d: '"\\\\' + d + '"', DYNAMICS[:12]))}, "\\\\sf", "\\\\sfz", "\\\\fp";
  articulations "-." staccato, "-!" staccatissimo, "->" accent, "-^" marcato, "--" tenuto; "\\\\fermata";
  bowing "\\\\downbow", "\\\\upbow"; ornaments "\\\\trill", "\\\\mordent", "\\\\prall", "\\\\turn";
  "\\\\breathe"; "\\\\arpeggio"; fingerings "-0" to "-5" (0 = open string);
  text directions "text:<words>" above the staff or "text_below:<words>" below (e.g. "text_below:cresc.",
  "text:riten.", "text:a tempo").
- changes: clef, key or time changes printed at the start of the bar, as "\\\\clef bass", "\\\\key d \\\\major",
  "\\\\time 3/4". Leave empty when nothing changes.
- notes: one short line listing what you corrected, or "no change".
"""


def ev_json(e: Ev) -> dict:
    return {"pitches": list(e.pitches), "duration": lily_duration(e.dur), "tie": e.tie, "grace": e.grace,
            "marks": list(e.marks)}


def bars_from_json(parts: list[dict]) -> tuple[list[tuple[Bar, ...]], list[str]]:
    """Validate a refined system. Bad pitches or durations are fatal; unknown marks are dropped."""
    problems: list[str] = []

    def ev_of(d: dict) -> Ev | None:
        bad = list(filter(lambda p: not PITCH_RE.match(p), d["pitches"]))
        try:
            dur = parse_duration(d["duration"])
        except ValueError:
            problems.append(f"fatal: duration {d['duration']!r}")
            return None
        if bad:
            problems.append(f"fatal: pitch {bad}")
            return None
        unknown = list(filter(lambda m: not valid_mark(m), d["marks"]))
        problems.extend(map(lambda m: f"dropped mark {m!r}", unknown))
        return Ev(tuple(d["pitches"]), dur, bool(d["tie"]), bool(d["grace"]),
                  tuple(dict.fromkeys(filter(valid_mark, d["marks"]))))

    def bar_of(d: dict) -> Bar:
        changes = tuple(filter(lambda c: CHANGE_RE.match(c), d["changes"]))
        problems.extend(map(lambda c: f"dropped change {c!r}", filter(lambda c: not CHANGE_RE.match(c), d["changes"])))
        return Bar(tuple(filter(None, map(ev_of, d["events"]))), changes)

    return list(map(lambda p: tuple(map(bar_of, p["bars"])), parts)), problems


def _png_block(im: Image.Image) -> dict:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                        "data": base64.standard_b64encode(buf.getvalue()).decode()}}


def system_image(strips: list[Image.Image]) -> Image.Image:
    w = max(map(lambda s: s.width, strips))
    canvas = Image.new("L", (w, sum(map(lambda s: s.height, strips))), 255)
    list(map(lambda ix: canvas.paste(strips[ix[0]], (0, ix[1])),
             zip(range(len(strips)), accumulate(map(lambda s: s.height, strips), initial=0))))
    return canvas


def halves(im: Image.Image) -> list[Image.Image]:
    """Left and right halves with 8 % overlap, upscaled so staff details stay legible."""
    w, h = im.size
    cut = lambda a, b: im.crop((int(a * w), 0, int(b * w), h))
    up = lambda c: c.resize((c.width * 2, c.height * 2), Image.LANCZOS) if c.width < 900 else c
    return [up(cut(0, 0.54)), up(cut(0.46, 1.0))]


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, u) -> None:
        self.input_tokens += u.input_tokens + (getattr(u, "cache_read_input_tokens", 0) or 0)
        self.output_tokens += u.output_tokens

    @property
    def usd(self) -> float:
        return round(self.input_tokens * PRICE_PER_MTOK[0] / 1e6 + self.output_tokens * PRICE_PER_MTOK[1] / 1e6, 4)


def ask_claude(client, model: str, system: str, messages: list, schema: dict, usage: Usage):
    r = client.beta.messages.create(
        model=model, max_tokens=16000, system=system, messages=messages,
        betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}})
    usage.add(r.usage)
    if r.stop_reason in ("refusal", "max_tokens"):
        return None, r
    return json.loads(next(filter(lambda b: b.type == "text", r.content)).text), r


def refine_system(client, model: str, score: Score, k: int, strips: list[Image.Image], usage: Usage) -> dict:
    """Ask Claude to correct system k. Returns {"bars": per-part bars or None, "log": ...}."""
    a, b = score.system_ranges()[k]
    draft = {"parts": list(map(lambda p: {"bars": list(map(lambda bar: {
        "changes": list(bar.changes), "events": list(map(ev_json, bar.events))}, p.bars[a:b]))}, score.parts))}
    context = (f"System {k + 1} of {len(score.breaks)}, starting at bar {a + 1}. Parts (top to bottom): "
               f"{len(score.parts)}. Key in force: {_prelude_at(score, 0, a)[1]}; metre {_prelude_at(score, 0, a)[2]}; "
               f"clefs {list(map(lambda p: _prelude_at(score, p, a)[0], range(len(score.parts))))}. "
               f"{'This is the first system: the first bar may be a pickup. ' if k == 0 else ''}"
               f"{'This is the last system: the final bar may be short. ' if k == len(score.breaks) - 1 else ''}"
               f"OMR draft:\n{json.dumps(draft, separators=(',', ':'))}")
    content = list(map(_png_block, halves(system_image(strips)))) + [{"type": "text", "text": context}]

    def check(parts: list[tuple[Bar, ...]]) -> list[str]:
        if len(parts) != len(score.parts) or len(set(map(len, parts))) != 1:
            return ["fatal: the number of parts or bars differs between parts"]
        spliced = replace(score, parts=tuple(map(lambda pb: Part(pb[0].clef, pb[0].bars[:a] + pb[1] + pb[0].bars[b:]),
                                                   zip(score.parts, parts))))
        rows = filter(lambda r: a < r["bar"] <= a + len(parts[0]), suspect_bars(bar_check(spliced)))
        return list(map(lambda r: f"bar {r['bar']} part {r['part']} lasts {r['got']} quarters, metre needs {r['expected']}",
                        rows))

    def attempt(messages: list, tries: int) -> dict:
        data, raw = ask_claude(client, model, REFINE_PROMPT, messages, SYSTEM_SCHEMA, usage)
        if data is None:
            return {"bars": None, "log": f"no answer ({raw.stop_reason})"}
        parts, problems = bars_from_json(data["parts"])
        errors = list(filter(lambda p: p.startswith("fatal"), problems)) + check(parts)
        if errors and tries > 0:
            retry = messages + [{"role": "assistant", "content": raw.content},
                                {"role": "user", "content": "Your answer has these problems; fix them and return the "
                                 "whole system again:\n- " + "\n- ".join(errors)}]
            return attempt(retry, tries - 1)
        fatal = any(map(lambda p: p.startswith("fatal"), errors))
        return {"bars": None if fatal else parts, "log": data["notes"], "problems": problems + errors}

    out = attempt([{"role": "user", "content": content}], 1)
    draft_bad = len(list(filter(lambda r: a < r["bar"] <= b, suspect_bars(bar_check(score)))))
    if out["bars"] is not None and len(list(filter(lambda p: "metre needs" in p, out.get("problems", [])))) > max(draft_bad, 0):
        out = {**out, "bars": None, "log": out["log"] + " (rejected: more bad bars than the draft)"}
    return {**out, "system": k + 1}


def refine_header(client, model: str, page: Image.Image, usage: Usage) -> dict | None:
    small = page.copy()
    small.thumbnail((1568, 1568))
    text = ("Read the printed header of this score page (ignore handwriting). Give title, subtitle, composer, "
            "arranger/editor line, tempo words (e.g. Andante), the metronome mark as beat duration (\"4\", \"4.\", "
            "\"2\") and bpm (use the lower number of a range; 0 if none), and whether the time signature is printed "
            "as numbers, C (common) or cut time. Empty string when absent.")
    data, _ = ask_claude(client, model, "You read printed sheet music.",
                         [{"role": "user", "content": [_png_block(small.convert("RGB")), {"type": "text", "text": text}]}],
                         HEADER_SCHEMA, usage)
    return data


def claude_pass(score: Score, systems: list[list[Image.Image]], page: Image.Image, model: str,
                workers: int = 4, client=None) -> tuple[Score, dict]:
    if client is None:
        import anthropic
        client = anthropic.Anthropic()
    usage = Usage()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        header_job = pool.submit(refine_header, client, model, page, usage)
        results = list(pool.map(lambda k: refine_system(client, model, score, k, systems[k], usage),
                                range(len(score.breaks))))
        header = header_job.result()
    ranges = score.system_ranges()
    chosen = list(map(lambda k: results[k]["bars"] or list(map(lambda p: p.bars[ranges[k][0]:ranges[k][1]],
                                                                score.parts)), range(len(ranges))))
    parts = tuple(map(lambda pi: Part(score.parts[pi].clef, tuple(chain.from_iterable(
        map(lambda c: c[pi], chosen)))), range(len(score.parts))))
    breaks = tuple(accumulate(map(lambda c: len(c[0]), chosen[:-1]), initial=0))
    refined = replace(score, parts=parts, breaks=breaks)
    if header:
        beat_ok = bool(header["tempo_beat"]) and bool(DUR_RE.match(header["tempo_beat"]))
        refined = replace(refined, title=header["title"] or refined.title, subtitle=header["subtitle"],
                          composer=header["composer"], arranger=header["arranger"], tempo_text=header["tempo_text"],
                          tempo=(header["tempo_beat"], header["tempo_bpm"]) if header["tempo_bpm"] > 0 and beat_ok
                          else refined.tempo, time_symbol=header["time_symbol"])
    log = {"model": model, "systems": list(map(
        lambda r: dict(filter(lambda kv: kv[0] != "bars", r.items())) | {"accepted": r["bars"] is not None}, results)),
        "header": header, "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
        "cost_usd": usage.usd}
    return refined, log


# ---------------------------------------------------------------- review sheet

def _font(size: int) -> ImageFont.ImageFont:
    paths = ("/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf")
    found = next(filter(lambda p: Path(p).exists(), paths), None)
    return ImageFont.truetype(found, size) if found else ImageFont.load_default()


def review_pdf(score: Score, systems: list[list[Image.Image]] | None, rows: list[dict], work: Path, out: Path) -> Path:
    """One block per system: the straightened photo staff above its engraving, suspect bars marked in red."""
    rdir = work / "review"
    shutil.rmtree(rdir, ignore_errors=True)
    rdir.mkdir(parents=True)
    suspects = set(map(lambda r: (r["part"], r["bar"]), suspect_bars(rows)))
    n = len(score.breaks)
    lys = list(map(lambda k: rdir / f"sys_{k:02d}.ly", range(n)))
    list(map(lambda k: lys[k].write_text(lilypond_source(score, (k,), review=True, suspects=suspects)), range(n)))
    subprocess.run(["lilypond", "-dno-point-and-click", "-dcrop", "--png", "-dresolution=130", "-o", str(rdir),
                    *map(str, lys)], capture_output=True, text=True, timeout=900)
    width = 1700
    fit = lambda im: im.resize((width, max(1, int(im.height * width / im.width))), Image.LANCZOS)

    def block(k: int) -> Image.Image:
        a, b = score.system_ranges()[k]
        engraved = rdir / f"sys_{k:02d}.cropped.png"
        eng = fit(Image.open(engraved).convert("L")) if engraved.exists() else Image.new("L", (width, 80), 255)
        photo = fit(system_image(systems[k])) if systems else Image.new("L", (width, 10), 255)
        bad = sorted(set(map(lambda r: r["bar"], filter(lambda r: a < r["bar"] <= b, suspect_bars(rows)))))
        label = f"System {k + 1}  ·  bars {a + 1}–{b}" + (f"  ·  CHECK bars {bad}" if bad else "")
        canvas = Image.new("RGB", (width, 46 + photo.height + eng.height + 30), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((10, 10), label, fill=(200, 0, 0) if bad else (0, 0, 0), font=_font(26))
        canvas.paste(photo.convert("RGB"), (0, 46))
        canvas.paste(eng.convert("RGB"), (0, 46 + photo.height + 10))
        draw.line((0, canvas.height - 6, width, canvas.height - 6), fill=(180, 180, 180), width=2)
        return canvas

    blocks = list(map(block, range(n)))
    page_h = int(width * 1.414)

    def paginate(pages: list, blk: Image.Image) -> list:
        used = sum(map(lambda b: b.height, pages[-1])) if pages else page_h
        return pages[:-1] + [pages[-1] + [blk]] if pages and used + blk.height <= page_h else pages + [[blk]]

    def render(group: list) -> Image.Image:
        page = Image.new("RGB", (width, page_h), "white")
        list(map(lambda bi: page.paste(group[bi[0]], (0, bi[1])),
                 zip(range(len(group)), accumulate(map(lambda b: b.height, group), initial=0))))
        return page

    pages = list(map(render, reduce(paginate, blocks, [])))
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=150)
    return out


# ---------------------------------------------------------------- comparison with a reference

def note_sequence(path: Path) -> list[tuple[int, Fraction]]:
    """(MIDI pitch, length in quarters) of every sounding note in order; tied notes count once."""
    if path.suffix.lower() in (".mid", ".midi"):
        import mido
        mf = mido.MidiFile(str(path))

        def step(acc: tuple, msg) -> tuple:
            t, active, notes = acc
            t += msg.time
            on = msg.type == "note_on" and msg.velocity > 0
            off = msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0)
            if on:
                return t, {**active, msg.note: t}, notes
            if off and msg.note in active:
                start = active[msg.note]
                rest = dict(filter(lambda kv: kv[0] != msg.note, active.items()))
                return t, rest, notes + [(start, msg.note, Fraction(t - start, mf.ticks_per_beat).limit_denominator(48))]
            return t, active, notes

        notes = chain.from_iterable(map(lambda tr: reduce(step, tr, (0, {}, []))[2], mf.tracks))
        return list(map(lambda n: (n[1], n[2]), sorted(notes, key=lambda n: (n[0], -n[1]))))
    import music21 as m21
    s = m21.converter.parse(str(path)).stripTies()
    part = s.parts[0] if s.parts else s
    return list(map(lambda n: (n.pitches[-1].midi, Fraction(n.quarterLength).limit_denominator(48)),
                    part.flatten().notes))


def compare(test: Path, truth: Path) -> dict:
    """Note-by-note agreement of two scores (MIDI or MusicXML), first part only; the top note of a chord counts."""
    a, b = note_sequence(truth), note_sequence(test)
    matched = lambda x, y: sum(map(lambda blk: blk.size, difflib.SequenceMatcher(a=x, b=y, autojunk=False)
                                   .get_matching_blocks()))
    pitch = matched(list(map(lambda t: t[0], a)), list(map(lambda t: t[0], b)))
    both = matched(a, b)
    return {"truth_notes": len(a), "test_notes": len(b), "pitch_match": pitch, "pitch_and_duration_match": both,
            "pitch_accuracy": round(pitch / max(1, len(a)), 4), "full_accuracy": round(both / max(1, len(a)), 4)}


# ---------------------------------------------------------------- driver

def page_images(src: Path, work: Path) -> list[Path]:
    """An image is one page; a scanned PDF is rasterised at 300 dpi, one image per page."""
    if src.suffix.lower() != ".pdf":
        return [src]
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "300", "-png", str(src), str(work / "page")], check=True)
    return sorted(work.glob("page-*.png"))


def convert(src: Path, out_root: Path, refine: str = "none", model: str = MODEL, use_audiveris: bool = True,
            audiveris: str | None = None, groups: str = DEFAULT_AUDIVERIS_GROUPS, title: str | None = None,
            composer: str | None = None, tempo: int | None = None, instrument: str = "acoustic grand",
            keep_homr_ornaments: bool = False) -> dict:
    out = out_root / src.stem
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)
    pages = page_images(src, work)
    homr_runs = list(map(lambda pg: run_homr(pg, work / pg.stem), pages))
    page_scores = list(map(lambda hr: from_musicxml(hr[0], keep_doubtful=keep_homr_ornaments), homr_runs))
    shutil.copy(homr_runs[0][0], out / f"{src.stem}.homr.musicxml")
    page_strips = list(map(lambda ps: strips_by_system(ps[1][1], len(ps[0].breaks), len(ps[0].parts)),
                           zip(page_scores, homr_runs)))
    systems = None if any(map(lambda s: s is None, page_strips)) else list(chain.from_iterable(page_strips))
    score = concat_scores(page_scores)
    score = replace(score, title=title or src.stem.replace("_", " ").replace("-", " ").title())
    report: dict = {"input": str(src), "pages": len(pages), "homr": {"systems": len(score.breaks),
                                                                    "parts": len(score.parts),
                                                                    "bars": len(score.parts[0].bars),
                                                                    "staff_images": systems is not None}}
    exe = find_audiveris(audiveris) if use_audiveris else None
    if use_audiveris and exe and systems:
        score, report["audiveris"] = audiveris_pass(score, systems, exe, work, set(groups.split(",")))
    elif use_audiveris:
        report["audiveris"] = {"status": "skipped: " + ("Audiveris not found" if not exe else "no staff images")}
    if refine == "claude":
        if systems is None:
            report["claude"] = {"status": "skipped: staff images do not line up with systems"}
        else:
            try:
                score, report["claude"] = claude_pass(score, systems, Image.open(pages[0]), model)
            except Exception as exc:  # no credentials or API failure: keep the unrefined score
                report["claude"] = {"status": f"failed: {type(exc).__name__}: {exc}"}
    score = tidy(replace(score, title=title or score.title, composer=composer or score.composer,
                         tempo=("4", tempo) if tempo else score.tempo))
    rows = bar_check(score)
    report["bars"] = {"total": len(score.parts[0].bars), "full": len(score.parts[0].bars) * len(score.parts) - len(rows),
                      "pickup_or_closing": len(list(filter(lambda r: r["kind"] in ("pickup", "closing"), rows))),
                      "suspect": suspect_bars(rows)}
    ly = out / f"{src.stem}.ly"
    ly.write_text(lilypond_source(score, instrument=instrument))
    warnings = run_lilypond(ly, out / src.stem)
    report["lilypond_warnings"] = list(filter(lambda l: "warning" in l, warnings.splitlines()))[:30]
    report["outputs"] = {"pdf": str(out / f"{src.stem}.pdf"), "midi": str(out / f"{src.stem}.midi"), "ly": str(ly),
                         "review": str(review_pdf(score, systems, rows, work, out / f"{src.stem}_review.pdf")),
                         "homr_musicxml": str(out / f"{src.stem}.homr.musicxml")}
    (out / "report.json").write_text(json.dumps(report, indent=1, default=str))
    return report


def summary_line(r: dict) -> str:
    if "error" in r:
        return f"{r['input']}: ERROR {r['error']}"
    b = r["bars"]
    extra = f"  claude ${r['claude'].get('cost_usd', 0)}" if isinstance(r.get("claude"), dict) and "cost_usd" in r["claude"] else ""
    marks = sum(map(lambda p: p.get("marks_added", 0), r.get("audiveris", {}).get("parts", [])))
    return (f"{Path(r['input']).name}: {b['total']} bars, {len(b['suspect'])} suspect, "
            f"{b['pickup_or_closing']} pickup/closing, audiveris marks {marks}{extra}\n  -> {r['outputs']['pdf']}\n"
            f"  -> review {r['outputs']['review']}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("convert", help="image(s) or scanned PDF(s) -> PDF, MIDI, LilyPond, review sheet")
    c.add_argument("inputs", nargs="+", type=Path)
    c.add_argument("--out", type=Path, default=Path("digitized_scores/from_image"))
    c.add_argument("--refine", choices=("none", "claude"), default="none",
                   help="claude: check every staff with the Claude API (needs ANTHROPIC_API_KEY or `ant auth login`)")
    c.add_argument("--model", default=MODEL)
    c.add_argument("--no-audiveris", action="store_true", help="skip the Audiveris markings pass")
    c.add_argument("--audiveris", default=None, help="path to the Audiveris executable")
    c.add_argument("--audiveris-marks", default=DEFAULT_AUDIVERIS_GROUPS,
                   help=f"mark groups taken from Audiveris: {','.join(MARK_GROUPS)},fingering,text")
    c.add_argument("--keep-homr-ornaments", action="store_true", help="keep homr's trills and breath marks")
    c.add_argument("--title")
    c.add_argument("--composer")
    c.add_argument("--tempo", type=int, help="quarter notes per minute for MIDI")
    c.add_argument("--instrument", default="acoustic grand", help="General MIDI instrument name, e.g. violin")
    k = sub.add_parser("compare", help="note agreement of an output with a trusted MIDI/MusicXML")
    k.add_argument("test", type=Path)
    k.add_argument("truth", type=Path)
    a = ap.parse_args(argv[1:])
    if a.cmd == "compare":
        print(json.dumps(compare(a.test, a.truth), indent=1))
        return 0

    def safe(p: Path) -> dict:
        try:
            return convert(p, a.out, a.refine, a.model, not a.no_audiveris, a.audiveris, a.audiveris_marks,
                           a.title, a.composer, a.tempo, a.instrument, a.keep_homr_ornaments)
        except Exception as exc:  # report and continue with the batch
            return {"input": str(p), "error": f"{type(exc).__name__}: {exc}"}

    results = list(map(safe, a.inputs))
    print("\n".join(map(summary_line, results)))
    return 1 if any(map(lambda r: "error" in r, results)) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

# <!-- APAF Bioinformatics | score_from_image.py | Approved | 2026-10-25 -->
