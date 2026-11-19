/* Karaoke stage: draws the current line as a treble staff with every note directly above its
   syllable, and lights the note and the word together from one shared column. */
(function () {
  "use strict";
  const K = (window.Karaoke = window.Karaoke || {});
  const NS = "http://www.w3.org/2000/svg";

  // Staff geometry (AGENTS.md Rule 2): five lines 12px apart, E4 at the bottom, G4 at y = 76.
  const LINE_GAP = 12;
  const E4_Y = 88;
  const F5_Y = 40;
  const HEAD_RX = 7;
  const HEAD_RY = 5;
  const STEM = 36;
  const SHARP_STEPS = [8, 5, 9, 6, 3, 7, 4];
  const FLAT_STEPS = [4, 7, 3, 6, 2, 5, 1];
  const SHARP_LETTERS = ["F", "C", "G", "D", "A", "E", "B"];
  const FLAT_LETTERS = ["B", "E", "A", "D", "G", "C", "F"];
  const LETTER_INDEX = { C: 0, D: 1, E: 2, F: 3, G: 4, A: 5, B: 6 };
  const SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const CLEF_PATH =
    "M 25 110 C 20 110 16 106 16 100 C 16 94 21 90 26 92 C 30 94 31 99 29 103 C 28 105 26 106 25 106 C 24 106 23 105 23 104 C 23 103 24 102 25 102 C 26 102 27 103 27 104 C 27 105 26 106 25 106 C 21 106 18 102 18 97 C 18 91 23 87 29 88 C 36 90 40 96 38 103 C 36 109 31 110 25 110 Z M 25 5 C 24 5 23 6 23 7 C 23 18 27 34 29 45 C 24 49 18 55 14 62 C 9 71 7 81 10 90 C 13 99 21 105 31 104 C 40 103 46 95 46 86 C 46 76 39 68 29 68 C 24 68 20 70 17 74 C 14 78 13 83 15 88 C 17 92 21 95 26 94 C 30 93 33 89 33 85 C 33 81 30 78 26 78 C 24 78 22 79 21 81 C 20 82 20 83 21 84 C 21 84 22 84 23 83 C 24 82 25 82 26 82 C 28 82 30 84 30 86 C 30 88 28 90 25 90 C 22 90 19 88 18 85 C 17 81 18 77 21 74 C 24 71 28 70 32 70 C 40 70 46 77 46 85 C 46 94 39 101 30 101 C 21 101 14 95 12 87 C 10 79 12 70 16 62 C 20 56 25 50 30 46 C 28 35 25 20 24 7 C 24 6 24 5 25 5 Z";

  const view = {
    el: null,
    tl: null,
    score: null,
    onSeek: null,
    phrase: -1,
    cols: [], // {ev, el, cx, line, lineEnd, fillRect, textWidth}
    colByOrder: new Map(),
    lines: [], // {svg, playhead}
    lastEvent: -2,
    fillRect: null,
    uid: 0,
  };

  const range = (n) => K.timeline.range(n);

  function svg(tag, attrs, parent, text) {
    const node = document.createElementNS(NS, tag);
    Object.keys(attrs || {}).forEach((k) => node.setAttribute(k, attrs[k]));
    if (text != null) node.textContent = text;
    if (parent) parent.appendChild(node);
    return node;
  }

  /* ---------- pitch helpers ---------- */

  function spell(ev) {
    const m = /^([A-G])([#b]?)(-?\d+)$/.exec(ev.pitch_name || "");
    if (m) return { letter: m[1], acc: m[2], octave: Number(m[3]) };
    const name = SHARP_NAMES[((ev.midi % 12) + 12) % 12];
    return { letter: name[0], acc: name[1] || "", octave: Math.floor(ev.midi / 12) - 1 };
  }

  const staffStep = (sp) => LETTER_INDEX[sp.letter] + sp.octave * 7 - 30; // E4 = 0
  const stepY = (step) => E4_Y - step * (LINE_GAP / 2);

  function keyAccidentals(fifths) {
    const letters = fifths >= 0 ? SHARP_LETTERS.slice(0, fifths) : FLAT_LETTERS.slice(0, -fifths);
    return new Map(letters.map((l) => [l, fifths >= 0 ? "#" : "b"]));
  }

  const ACC_GLYPH = { "#": "♯", b: "♭", "": "♮" };

  /* ---------- layout ---------- */

  function lyricFont() {
    const style = getComputedStyle(view.el);
    return { size: parseFloat(style.getPropertyValue("--lyric-size")) || 24, family: style.getPropertyValue("--lyric-font") || "Georgia, serif" };
  }

  function measurer(font) {
    const ctx = document.createElement("canvas").getContext("2d");
    ctx.font = "600 " + font.size + "px " + font.family;
    return (text) => ctx.measureText(text).width;
  }

  function columnOf(ev, measure) {
    const textWidth = ev.lyric ? measure(ev.lyric) : 0;
    const natural = ev.kind === "R" ? 26 : 30 + Math.min(ev.dur_q, 2) * 14;
    return { ev, textWidth, width: Math.max(natural, textWidth + 14) };
  }

  /* Every column is a unit; the last column of a bar carries the bar line. */
  function segmentsOf(bar, measure) {
    return bar.events.map((ev, i) => {
      const col = columnOf(ev, measure);
      const endsBar = i === bar.events.length - 1;
      return { cols: [col], bar, endsBar, width: col.width + (endsBar ? 18 : 0) };
    });
  }

  const widthOf = (segments) => segments.reduce((sum, s) => sum + s.width, 0);

  /* Greedy fill. When a line overflows, break at the last bar line if that leaves both lines well filled. */
  function packLines(segments, firstAvail, restAvail) {
    return segments
      .reduce(
        (lines, seg) => {
          const line = lines[lines.length - 1];
          const avail = lines.length === 1 ? firstAvail : restAvail;
          if (line.length === 0 || widthOf(line) + seg.width <= avail) {
            line.push(seg);
            return lines;
          }
          const cut = line.map((s) => s.endsBar).lastIndexOf(true) + 1;
          const keepsEnough = widthOf(line.slice(0, cut)) >= avail * 0.55;
          const tail = cut > 0 && keepsEnough && widthOf(line.slice(cut)) < avail * 0.45 ? line.splice(cut) : [];
          return lines.concat([tail.concat([seg])]);
        },
        [[]]
      )
      .filter((line) => line.length)
      .map((line) => ({ segments: line, width: widthOf(line) }));
  }

  function prefixWidths(fifths, withTime) {
    const keyW = Math.abs(fifths) * 11;
    const timeX = 50 + keyW + 8;
    const barX = withTime ? timeX + 28 : 50 + keyW + 10;
    return { keyW, timeX, barX, startX: barX + 14 };
  }

  /* ---------- drawing ---------- */

  function drawPrefix(g, fifths, timeSig, withTime) {
    const p = prefixWidths(fifths, withTime);
    svg("path", { d: CLEF_PATH, class: "ink", transform: "translate(6 -9) scale(0.86)" }, g);
    const steps = fifths >= 0 ? SHARP_STEPS : FLAT_STEPS;
    range(Math.abs(fifths)).forEach((i) =>
      svg("text", { x: 50 + i * 11, y: stepY(steps[i]) + 7, class: "accidental keysig" }, g, fifths >= 0 ? ACC_GLYPH["#"] : ACC_GLYPH.b)
    );
    if (withTime) {
      const parts = String(timeSig || "4/4").split("/");
      svg("text", { x: p.timeX + 10, y: F5_Y + 22, class: "timesig" }, g, parts[0]);
      svg("text", { x: p.timeX + 10, y: F5_Y + 46, class: "timesig" }, g, parts[1] || "4");
    }
    svg("line", { x1: p.barX, x2: p.barX, y1: F5_Y, y2: E4_Y, class: "barline" }, g);
    return p;
  }

  function drawRest(g, ev, cx) {
    const d = ev.duration;
    if (d === "whole") return svg("rect", { x: cx - 8, y: F5_Y + LINE_GAP, width: 16, height: 6, class: "ink" }, g);
    if (d === "half") return svg("rect", { x: cx - 8, y: F5_Y + 2 * LINE_GAP - 6, width: 16, height: 6, class: "ink" }, g);
    if (d === "quarter")
      return svg("path", { d: `M ${cx - 3} 48 L ${cx + 4} 58 L ${cx - 3} 66 L ${cx + 4} 76 C ${cx - 4} 73 ${cx - 5} 80 ${cx + 1} 84`, class: "ink-stroke rest-stroke" }, g);
    const dots = d === "16th" ? [58, 70] : [58];
    dots.forEach((y) => {
      svg("circle", { cx: cx - 3, cy: y, r: 3, class: "ink" }, g);
      svg("path", { d: `M ${cx - 3} ${y + 2} Q ${cx + 3} ${y + 2} ${cx + 6} ${y - 4}`, class: "ink-stroke" }, g);
    });
    return svg("line", { x1: cx + 6, y1: 54, x2: cx - 1, y2: d === "16th" ? 88 : 80, class: "ink-stroke" }, g);
  }

  function drawNote(g, col, keyAcc, beam) {
    const ev = col.ev;
    const sp = spell(ev);
    const step = staffStep(sp);
    const y = stepY(step);
    const cx = col.cx;
    const hollow = ev.duration === "half" || ev.duration === "whole";
    const up = beam ? beam.up : step < 4;

    range(step <= -2 ? Math.floor(-step / 2) : 0).forEach((i) => svg("line", { x1: cx - 11, x2: cx + 11, y1: stepY(-2 - 2 * i), y2: stepY(-2 - 2 * i), class: "ledger" }, g));
    range(step >= 10 ? Math.floor((step - 8) / 2) : 0).forEach((i) => svg("line", { x1: cx - 11, x2: cx + 11, y1: stepY(10 + 2 * i), y2: stepY(10 + 2 * i), class: "ledger" }, g));

    if ((keyAcc.get(sp.letter) || "") !== sp.acc) svg("text", { x: cx - 19, y: y + 7, class: "accidental" }, g, ACC_GLYPH[sp.acc]);

    svg("ellipse", { cx, cy: y, rx: HEAD_RX, ry: HEAD_RY, transform: `rotate(-20 ${cx} ${y})`, class: hollow ? "head hollow" : "head ink" }, g);
    if (ev.has_dot) svg("circle", { cx: cx + 12, cy: step % 2 === 0 ? y - 3 : y, r: 2, class: "ink" }, g);

    if (ev.duration !== "whole") {
      const sx = up ? cx + HEAD_RX - 0.8 : cx - HEAD_RX + 0.8;
      const tip = beam ? beam.y : up ? y - STEM : y + STEM;
      svg("line", { x1: sx, x2: sx, y1: y, y2: tip, class: "stem" }, g);
      const flags = beam ? 0 : ev.duration === "eighth" ? 1 : ev.duration === "16th" ? 2 : 0;
      range(flags).forEach((i) => {
        const fy = up ? tip + i * 7 : tip - i * 7;
        const dir = up ? 1 : -1;
        svg("path", { d: `M ${sx} ${fy} C ${sx + 2} ${fy + dir * 8} ${sx + 12} ${fy + dir * 10} ${sx + 8} ${fy + dir * 20}`, class: "ink-stroke flag" }, g);
      });
    }
    col.noteY = y;
    col.stemUp = up;
  }

  /* Consecutive eighths/sixteenths inside one beat share a flat beam. */
  function beamGroups(lineCols, beatLen) {
    const short = (c) => c.ev.kind === "N" && (c.ev.duration === "eighth" || c.ev.duration === "16th");
    const groupKey = (c) => c.barStart + ":" + Math.floor((c.ev.onset_q - c.barStart) / beatLen + 1e-6);
    return lineCols
      .reduce((groups, c) => {
        const last = groups[groups.length - 1];
        if (short(c) && last && last.key === groupKey(c) && last.open) {
          last.cols.push(c);
          return groups;
        }
        return groups.concat([{ key: groupKey(c), cols: short(c) ? [c] : [], open: short(c) }]);
      }, [])
      .filter((grp) => grp.cols.length >= 2);
  }

  function beamShape(grp) {
    const steps = grp.cols.map((c) => staffStep(spell(c.ev)));
    const up = steps.reduce((a, b) => a + b, 0) / steps.length < 4;
    const ys = steps.map(stepY);
    return { cols: grp.cols, up, y: up ? Math.min.apply(null, ys) - STEM : Math.max.apply(null, ys) + STEM };
  }

  function drawBeam(g, beam) {
    const { cols, up, y } = beam;
    const sx = (c) => (up ? c.cx + HEAD_RX - 0.8 : c.cx - HEAD_RX + 0.8);
    svg("line", { x1: sx(cols[0]), x2: sx(cols[cols.length - 1]), y1: y, y2: y, class: "beam" }, g);
    const y2 = up ? y + 7 : y - 7;
    cols.forEach((c, i) => {
      if (c.ev.duration !== "16th") return;
      const next = cols[i + 1];
      const prev = cols[i - 1];
      if (next && next.ev.duration === "16th") svg("line", { x1: sx(c), x2: sx(next), y1: y2, y2, class: "beam" }, g);
      else if (!(prev && prev.ev.duration === "16th")) svg("line", { x1: sx(c), x2: sx(c) + (next ? 9 : -9), y1: y2, y2, class: "beam" }, g);
    });
  }

  function drawTies(g, lineCols, lineEndX) {
    lineCols
      .filter((c) => c.ev.kind === "N" && c.ev.tie_start)
      .forEach((c) => {
        const next = lineCols[lineCols.indexOf(c) + 1];
        const x1 = c.cx + 6;
        const x2 = next && next.ev.kind === "N" ? next.cx - 6 : lineEndX - 4;
        const dir = c.stemUp ? 1 : -1;
        const y = c.noteY + dir * 8;
        svg("path", { d: `M ${x1} ${y} Q ${(x1 + x2) / 2} ${y + dir * 9} ${x2} ${y}`, class: "tie" }, g);
      });
    const first = lineCols[0];
    if (first && first.ev.kind === "N" && first.ev.tie_stop && view.cols.length && view.cols[view.cols.length - 1].line !== first.line) {
      const dir = first.stemUp ? 1 : -1;
      const y = first.noteY + dir * 8;
      svg("path", { d: `M ${first.cx - 22} ${y} Q ${first.cx - 14} ${y + dir * 7} ${first.cx - 6} ${y}`, class: "tie" }, g);
    }
  }

  function drawLine(line, lineIndex, width, font, keyAcc) {
    const fifths = view.score.fifths || 0;
    const lyricY = 138 + font.size * 0.5;
    const height = Math.ceil(lyricY + font.size * 0.5);
    const root = svg("svg", { class: "system", width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Staff line " + (lineIndex + 1) }, view.el);
    range(5).forEach((i) => svg("line", { x1: 4, x2: width - 4, y1: F5_Y + i * LINE_GAP, y2: F5_Y + i * LINE_GAP, class: "staffline" }, root));
    const prefix = drawPrefix(root, fifths, view.score.time_signature, lineIndex === 0);

    const avail = width - prefix.startX - 8;
    const stretch = line.last && line.width < avail * 0.7 ? 1 : Math.min(1.7, avail / line.width);
    const placed = line.segments.reduce(
      (acc, seg) => {
        const cols = seg.cols.reduce(
          (a, col) => {
            const w = col.width * stretch;
            const item = Object.assign({}, col, { w, x: a.x, cx: a.x + w / 2, line: lineIndex, barStart: seg.bar.start_q });
            return { x: a.x + w, cols: a.cols.concat([item]) };
          },
          { x: acc.x, cols: [] }
        );
        const barX = seg.endsBar ? cols.x + 9 * stretch : null;
        return { x: seg.endsBar ? cols.x + 18 * stretch : cols.x, cols: acc.cols.concat(cols.cols), bars: barX == null ? acc.bars : acc.bars.concat([barX]) };
      },
      { x: prefix.startX, cols: [], bars: [] }
    );
    placed.bars.forEach((x) => svg("line", { x1: x, x2: x, y1: F5_Y, y2: E4_Y, class: "barline" }, root));

    const beamList = beamGroups(placed.cols, view.tl.beatLen).map(beamShape);
    const beams = new Map(beamList.flatMap((bm) => bm.cols.map((c) => [c.ev.event_index, bm])));

    placed.cols.reduce((rightEdge, col, i) => {
      const prev = placed.cols[i - 1];
      const symbol = col.ev.chord_symbol;
      if (!symbol || (prev && prev.ev.chord_symbol === symbol)) return rightEdge;
      const x = Math.max(col.x + 2, rightEdge + 8);
      svg("text", { x, y: 16, class: "chord-symbol" }, root, symbol);
      return x + symbol.length * 8.6;
    }, 0);

    placed.cols.forEach((col) => {
      const ev = col.ev;

      const g = svg("g", { class: "col" + (ev.kind === "R" ? " rest" : ""), "data-ev": ev.event_index, "data-word": ev.word, "data-q": ev.onset_q }, root);
      svg("rect", { x: col.x + 1, y: 24, width: Math.max(4, col.w - 2), height: height - 26, rx: 9, class: "band" }, g);
      if (ev.kind === "R") drawRest(g, ev, col.cx);
      else drawNote(g, col, keyAcc, beams.get(ev.event_index));
      if (ev.lyric) {
        const clipId = "kclip" + (view.uid += 1);
        const clip = svg("clipPath", { id: clipId }, g);
        col.fillRect = svg("rect", { x: col.cx - col.textWidth / 2 - 1, y: lyricY - font.size, width: 0, height: font.size * 1.4 }, clip);
        svg("text", { x: col.cx, y: lyricY, class: "syllable" }, g, ev.lyric);
        svg("text", { x: col.cx, y: lyricY, class: "syllable-fill", "clip-path": `url(#${clipId})`, "aria-hidden": "true" }, g, ev.lyric);
      }
      svg("rect", { x: col.x, y: 20, width: col.w, height: height - 20, class: "hit" }, g);
      col.el = g;
      col.lineEnd = placed.x;
    });

    beamList.forEach((bm) => drawBeam(root, bm));
    drawTies(root, placed.cols, placed.x);
    const playhead = svg("line", { x1: 0, x2: 0, y1: 26, y2: E4_Y + 14, class: "playhead" }, root);
    view.lines.push({ svg: root, playhead });
    placed.cols.forEach((c) => {
      view.cols.push(c);
      view.colByOrder.set(c.ev.order, c);
    });
  }

  function renderPhrase(phrase) {
    const el = view.el;
    el.textContent = "";
    view.cols = [];
    view.colByOrder = new Map();
    view.lines = [];
    view.fillRect = null;
    view.lastEvent = -2;
    view.activeLine = -1;
    view.phrase = phrase.order;

    const width = Math.max(280, Math.floor(el.clientWidth));
    const font = lyricFont();
    const measure = measurer(font);
    const fifths = view.score.fifths || 0;
    const firstAvail = width - prefixWidths(fifths, true).startX - 8;
    const restAvail = width - prefixWidths(fifths, false).startX - 8;
    const events = view.tl.events.filter((e) => e.phrase === phrase.order);
    const bars = view.tl.bars
      .filter((b) => b.phrase === phrase.order)
      .map((b) => Object.assign({}, b, { events: events.filter((e) => e.onset_q >= b.start_q - 1e-6 && e.onset_q < b.start_q + b.dur_q - 1e-6) }));
    const segments = bars.flatMap((b) => segmentsOf(b, measure));
    const lines = packLines(segments, firstAvail, restAvail);
    const keyAcc = keyAccidentals(fifths);
    lines.forEach((line, i) => drawLine(Object.assign(line, { last: i === lines.length - 1 }), i, width, font, keyAcc));
    el.classList.remove("enter");
    void el.offsetWidth;
    el.classList.add("enter");
  }

  /* ---------- per-frame update ---------- */

  function syncClasses(q, active) {
    const word = active && active.word >= 0 ? active.word : -1;
    view.cols.forEach((c) => {
      const ev = c.ev;
      const isActive = !!active && ev.order === active.order;
      const cl = c.el.classList;
      cl.toggle("active", isActive);
      cl.toggle("in-word", !isActive && word >= 0 && ev.word === word);
      cl.toggle("sung", !isActive && ev.word !== word && ev.onset_q + ev.dur_q <= q + 1e-6);
      if (c.fillRect && ev.word !== word) c.fillRect.setAttribute("width", 0);
    });
  }

  function movePlayhead(q, ev) {
    const col = ev ? view.colByOrder.get(ev.order) : view.cols[0];
    view.lines.forEach((l, i) => l.playhead.classList.toggle("on", !!col && i === col.line));
    if (!col) return;
    if (col.line !== view.activeLine) {
      view.activeLine = col.line;
      if (view.follow && view.lines.length > 1) view.lines[col.line].svg.scrollIntoView({ block: "center", behavior: view.reduced ? "auto" : "smooth" });
    }
    const next = view.colByOrder.get(col.ev.order + 1);
    const toX = next && next.line === col.line ? next.cx : col.lineEnd;
    const frac = ev ? Math.min(1, Math.max(0, (q - ev.onset_q) / Math.max(ev.dur_q, 1e-6))) : 0;
    const x = col.cx + (toX - col.cx) * frac;
    view.lines[col.line].playhead.setAttribute("transform", `translate(${x.toFixed(1)} 0)`);
  }

  function update(q) {
    const tl = view.tl;
    if (!tl) return null;
    const pos = Math.min(Math.max(0, q), Math.max(0, tl.total - 1e-6));
    const phrase = tl.phraseAt(pos);
    if (!phrase) return null;
    if (phrase.order !== view.phrase) renderPhrase(phrase);

    const ev = tl.eventAt(pos);
    const sounding = ev && pos < ev.onset_q + ev.dur_q ? ev : null;
    if ((sounding ? sounding.order : -1) !== view.lastEvent) {
      view.lastEvent = sounding ? sounding.order : -1;
      syncClasses(pos, sounding);
    }
    const word = tl.wordAt(pos);
    if (word) {
      const col = view.cols.find((c) => c.fillRect && c.ev.word === word.order);
      if (col) col.fillRect.setAttribute("width", ((col.textWidth + 2) * Math.min(1, (pos - word.start_q) / Math.max(word.end_q - word.start_q, 1e-6))).toFixed(1));
    }
    movePlayhead(pos, ev && ev.phrase === phrase.order ? ev : null);
    return { phrase, event: sounding, word };
  }

  function onClick(e) {
    const g = e.target.closest ? e.target.closest(".col") : null;
    if (!g || !view.onSeek) return;
    const word = view.tl.words[Number(g.getAttribute("data-word"))];
    view.onSeek(word ? word.start_q : Number(g.getAttribute("data-q")));
  }

  K.stage = {
    init: (el, onSeek) => {
      view.el = el;
      view.onSeek = onSeek;
      el.addEventListener("click", onClick);
    },
    setScore: (score, tl) => {
      view.score = score;
      view.tl = tl;
      view.phrase = -1;
    },
    relayout: () => {
      view.phrase = -1;
    },
    setFollow: (on) => {
      view.follow = on;
      view.reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    },
    update,
  };
})();
