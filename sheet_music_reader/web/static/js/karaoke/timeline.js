/* Karaoke timeline: flatten one arrangement mode into sorted tracks with fast lookups by time. */
(function () {
  "use strict";
  const K = (window.Karaoke = window.Karaoke || {});

  /* Index of the last item whose key(item) <= q, or -1. Items must be sorted by key. */
  function lastAtOrBefore(items, key, q) {
    const step = (lo, hi) => {
      if (lo > hi) return hi;
      const mid = (lo + hi) >> 1;
      return key(items[mid]) <= q ? step(mid + 1, hi) : step(lo, mid - 1);
    };
    return step(0, items.length - 1);
  }

  /* Index of the first item whose key(item) >= q (items.length if none). */
  function firstAtOrAfter(items, key, q) {
    const i = lastAtOrBefore(items, key, q);
    return i >= 0 && key(items[i]) === q ? firstEqual(items, key, q, i) : i + 1;
  }
  function firstEqual(items, key, q, i) {
    return i > 0 && key(items[i - 1]) === q ? firstEqual(items, key, q, i - 1) : i;
  }

  function beatLength(beats, beatType) {
    const compound = beatType === 8 && beats % 3 === 0 && beats >= 6;
    return compound ? 1.5 : 4 / beatType;
  }

  function range(n) {
    return Array.from({ length: Math.max(0, n) }, (_, i) => i);
  }

  function barClicks(bar) {
    const len = beatLength(bar.beats, bar.beat_type);
    return range(Math.round(bar.dur_q / len + 1e-6)).map((i) => ({ q: bar.start_q + i * len, accent: i === 0, beat: i }));
  }

  /* One sounding pulse per beat of every chord: bass on the first, chord tones on all. */
  function chordPulses(chord, beatLen) {
    const count = Math.max(1, Math.round((chord.end_q - chord.onset_q) / beatLen + 1e-6));
    return range(count).map((i) => ({
      q: chord.onset_q + i * beatLen,
      dur_q: Math.min(beatLen, chord.end_q - (chord.onset_q + i * beatLen)),
      bass: i === 0 ? chord.bass_midi : null,
      bassDur_q: chord.end_q - chord.onset_q,
      midis: chord.chord_midis || [],
      first: i === 0,
    }));
  }

  function build(mode) {
    const phrases = mode.phrases.map((p, i) => Object.assign({}, p, { order: i }));
    const bars = phrases.flatMap((p) => p.bars.map((b) => Object.assign({}, b, { phrase: p.order })));
    const events = phrases
      .flatMap((p) => p.bars.flatMap((b) => b.events.map((e) => Object.assign({}, e, { phrase: p.order }))))
      .sort((a, b) => a.onset_q - b.onset_q);
    const words = phrases
      .flatMap((p) => p.words.map((w) => Object.assign({}, w, { phrase: p.order })))
      .sort((a, b) => a.start_q - b.start_q)
      .map((w, i) => Object.assign(w, { order: i }));
    const wordOfEvent = new Map(words.flatMap((w) => w.event_indices.map((ev) => [ev, w.order])));
    events.forEach((e, i) => {
      e.order = i;
      e.word = wordOfEvent.has(e.event_index) ? wordOfEvent.get(e.event_index) : -1;
    });
    const firstBar = bars[0] || { beats: 4, beat_type: 4, dur_q: 4 };
    const beatLen = beatLength(firstBar.beats, firstBar.beat_type);
    const chords = (mode.chords || []).slice().sort((a, b) => a.onset_q - b.onset_q);
    const sounding = events.filter((e) => e.kind === "N" && !e.tie_stop && e.midi != null);
    const total = mode.total_beats_q || (bars.length ? bars[bars.length - 1].start_q + bars[bars.length - 1].dur_q : 0);

    return {
      id: mode.mode_id,
      label: mode.label,
      total,
      beatLen,
      barLen: firstBar.dur_q,
      beatsPerBar: Math.round(firstBar.dur_q / beatLen),
      phrases,
      bars,
      events,
      words,
      chords,
      sounding,
      clicks: bars.flatMap(barClicks),
      backing: chords.flatMap((c) => chordPulses(c, beatLen)),
      eventAt: (q) => events[lastAtOrBefore(events, (e) => e.onset_q, q)] || null,
      chordAt: (q) => {
        const c = chords[lastAtOrBefore(chords, (x) => x.onset_q, q)];
        return c && q < c.end_q ? c : null;
      },
      phraseAt: (q) => phrases[Math.max(0, lastAtOrBefore(phrases, (p) => p.start_q, q))] || null,
      wordAt: (q) => {
        const w = words[lastAtOrBefore(words, (x) => x.start_q, q)];
        return w && q < w.end_q ? w : null;
      },
      barAt: (q) => bars[Math.max(0, lastAtOrBefore(bars, (b) => b.start_q, q))] || null,
    };
  }

  K.timeline = { build, lastAtOrBefore, firstAtOrAfter, beatLength, range };
})();
