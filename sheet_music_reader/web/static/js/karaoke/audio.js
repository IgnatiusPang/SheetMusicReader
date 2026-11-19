/* Karaoke audio: guide melody, chord backing and beat click, all scheduled on the WebAudio clock.
   The audio clock is the only clock; position() is what every highlight is drawn from. */
(function () {
  "use strict";
  const K = (window.Karaoke = window.Karaoke || {});
  const LOOKAHEAD_S = 0.12;
  const TICK_MS = 25;
  const START_DELAY_S = 0.06;

  const state = {
    ctx: null,
    buses: null,
    tl: null,
    qpm: 72,
    transpose: 0,
    playing: false,
    anchorQ: 0, // song position (quarters) at time anchorT
    anchorT: 0,
    prevAnchor: null, // anchor in force until a scheduled loop wrap is reached
    pausedQ: 0,
    cursors: { guide: 0, backing: 0, click: 0 },
    loop: null, // {start, end} in quarters
    timer: null,
    live: new Set(),
    volumes: { guide: 0.8, backing: 0.65, click: 0.3 },
    onEnd: null,
  };
  const counts = { guide: 0, backing: 0, click: 0 };

  const hz = (midi) => 440 * Math.pow(2, (midi - 69) / 12);
  const qps = () => state.qpm / 60;

  function ensureContext() {
    if (state.ctx) return state.ctx;
    const Ctx = window.AudioContext || window.webkitAudioContext;
    const ctx = new Ctx();
    const master = ctx.createGain();
    const limiter = ctx.createDynamicsCompressor();
    limiter.threshold.value = -10;
    limiter.ratio.value = 6;
    master.connect(limiter);
    limiter.connect(ctx.destination);
    const bus = (name) => {
      const g = ctx.createGain();
      g.gain.value = state.volumes[name];
      g.connect(master);
      return g;
    };
    state.ctx = ctx;
    state.buses = { master, guide: bus("guide"), backing: bus("backing"), click: bus("click") };
    return ctx;
  }

  function track(node, stopAt) {
    state.live.add(node);
    node.onended = () => state.live.delete(node);
    node.stop(stopAt);
  }

  /* One enveloped oscillator into a bus. */
  function tone(busName, type, freq, when, dur, peak, attack, release, cutoff) {
    const ctx = state.ctx;
    const osc = ctx.createOscillator();
    const env = ctx.createGain();
    const filter = ctx.createBiquadFilter();
    osc.type = type;
    osc.frequency.value = freq;
    filter.type = "lowpass";
    filter.frequency.value = cutoff;
    const end = when + Math.max(dur, attack + 0.02);
    env.gain.setValueAtTime(0.0001, when);
    env.gain.linearRampToValueAtTime(peak, when + attack);
    env.gain.setValueAtTime(peak, Math.max(when + attack, end - release));
    env.gain.exponentialRampToValueAtTime(0.0001, end + release);
    osc.connect(filter);
    filter.connect(env);
    env.connect(state.buses[busName]);
    osc.start(when);
    track(osc, end + release + 0.02);
  }

  /* Plucked tone that decays on its own: used for the backing so it sits behind the voice. */
  function pluck(freq, when, dur, peak, type) {
    const ctx = state.ctx;
    const osc = ctx.createOscillator();
    const env = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    env.gain.setValueAtTime(0.0001, when);
    env.gain.linearRampToValueAtTime(peak, when + 0.012);
    env.gain.exponentialRampToValueAtTime(peak * 0.25, when + Math.max(0.08, dur * 0.6));
    env.gain.exponentialRampToValueAtTime(0.0001, when + dur + 0.12);
    osc.connect(env);
    env.connect(state.buses.backing);
    osc.start(when);
    track(osc, when + dur + 0.16);
  }

  function playGuide(ev, when) {
    const dur = Math.max(0.08, (ev.sound_dur_q || ev.dur_q) / qps() - 0.03);
    const f = hz(ev.midi + state.transpose);
    tone("guide", "triangle", f, when, dur, 0.5, 0.03, 0.07, 2600);
    tone("guide", "sine", f * 2, when, dur, 0.1, 0.03, 0.07, 4000);
    counts.guide += 1;
  }

  function playBacking(pulse, when) {
    const beat = pulse.dur_q / qps();
    if (pulse.bass != null) pluck(hz(pulse.bass + state.transpose), when, Math.min(pulse.bassDur_q / qps(), 2.4), 0.34, "triangle");
    pulse.midis.forEach((m) => pluck(hz(m + state.transpose), when, beat * 0.9, pulse.first ? 0.14 : 0.09, "sine"));
    counts.backing += 1;
  }

  function playClick(accent, when) {
    tone("click", "square", accent ? 1560 : 1040, when, 0.03, accent ? 0.5 : 0.3, 0.002, 0.03, 6000);
    counts.click += 1;
  }

  function timeOf(q, anchor) {
    return anchor.t + (q - anchor.q) / qps();
  }

  /* Schedule every item of one track that starts in [fromQ, toQ). */
  function scheduleTrack(name, items, key, fromQ, toQ, anchor, play) {
    const start = state.cursors[name];
    const end = K.timeline.firstAtOrAfter(items, key, toQ);
    items.slice(start, Math.max(start, end)).forEach((item) => play(item, Math.max(state.ctx.currentTime, timeOf(key(item), anchor))));
    state.cursors[name] = Math.max(start, end);
  }

  function scheduleWindow(fromQ, toQ, anchor) {
    const tl = state.tl;
    scheduleTrack("guide", tl.sounding, (e) => e.onset_q, fromQ, toQ, anchor, playGuide);
    scheduleTrack("backing", tl.backing, (p) => p.q, fromQ, toQ, anchor, playBacking);
    scheduleTrack("click", tl.clicks, (c) => c.q, fromQ, toQ, anchor, (c, when) => playClick(c.accent, when));
  }

  function resetCursors(q) {
    const tl = state.tl;
    state.cursors.guide = K.timeline.firstAtOrAfter(tl.sounding, (e) => e.onset_q, q);
    state.cursors.backing = K.timeline.firstAtOrAfter(tl.backing, (p) => p.q, q);
    state.cursors.click = K.timeline.firstAtOrAfter(tl.clicks, (c) => c.q, q);
  }

  function currentAnchor() {
    return { q: state.anchorQ, t: state.anchorT };
  }

  function tick() {
    if (!state.playing) return;
    const now = state.ctx.currentTime;
    if (state.prevAnchor && now >= state.anchorT) state.prevAnchor = null;
    const anchor = currentAnchor();
    const horizonQ = anchor.q + (now + LOOKAHEAD_S - anchor.t) * qps();
    const limit = state.loop ? state.loop.end : state.tl.total;

    if (horizonQ < limit) {
      scheduleWindow(0, horizonQ, anchor);
      return;
    }
    scheduleWindow(0, limit, anchor);
    if (state.loop && !state.prevAnchor) {
      // Wrap exactly on the beat: the new anchor takes over when the loop end is reached.
      state.prevAnchor = anchor;
      state.anchorT = timeOf(limit, anchor);
      state.anchorQ = state.loop.start;
      resetCursors(state.loop.start);
      return;
    }
    if (!state.loop && position() >= state.tl.total) {
      pause();
      state.pausedQ = 0;
      if (state.onEnd) state.onEnd();
    }
  }

  function position() {
    if (!state.playing || !state.ctx) return state.pausedQ;
    const now = state.ctx.currentTime;
    const a = state.prevAnchor && now < state.anchorT ? state.prevAnchor : currentAnchor();
    return a.q + (now - a.t) * qps();
  }

  function silence() {
    const now = state.ctx.currentTime;
    const gate = state.buses.master.gain;
    gate.cancelScheduledValues(now);
    gate.setValueAtTime(gate.value, now);
    gate.linearRampToValueAtTime(0, now + 0.03);
    Array.from(state.live).forEach((node) => {
      try {
        node.stop(now + 0.04);
      } catch (_err) {
        /* already stopped */
      }
    });
    state.live.clear();
    gate.setValueAtTime(1, now + 0.06);
  }

  function countInClicks(startT, bars) {
    const tl = state.tl;
    const beat = tl.beatLen / qps();
    K.timeline.range(tl.beatsPerBar * bars).forEach((i) => playClick(i % tl.beatsPerBar === 0, startT + i * beat));
    return tl.beatsPerBar * bars * beat;
  }

  function play(opts) {
    if (!state.tl) return Promise.resolve();
    const ctx = ensureContext();
    const fromQ = Math.min(Math.max(0, state.pausedQ), Math.max(0, state.tl.total - 0.001));
    return Promise.resolve(ctx.state === "suspended" ? ctx.resume() : null).then(() => {
      if (state.playing) return;
      const startT = ctx.currentTime + START_DELAY_S;
      const lead = opts && opts.countIn ? countInClicks(startT, 1) : 0;
      state.anchorQ = fromQ;
      state.anchorT = startT + lead;
      state.prevAnchor = null;
      resetCursors(fromQ);
      state.playing = true;
      state.timer = window.setInterval(tick, TICK_MS);
      tick();
    });
  }

  function pause() {
    if (!state.playing) return;
    state.pausedQ = Math.max(0, position());
    state.playing = false;
    window.clearInterval(state.timer);
    state.timer = null;
    state.prevAnchor = null;
    silence();
  }

  function seek(q) {
    const target = Math.min(Math.max(0, q), state.tl ? state.tl.total : 0);
    state.pausedQ = target;
    if (!state.playing) return;
    silence();
    state.anchorQ = target;
    state.anchorT = state.ctx.currentTime + START_DELAY_S;
    state.prevAnchor = null;
    resetCursors(target);
  }

  function setTempo(qpm) {
    const q = position();
    state.qpm = qpm;
    if (!state.playing) return;
    // Re-anchor at the current position. Cursors stay: everything before them is already scheduled.
    state.anchorQ = q;
    state.anchorT = state.ctx.currentTime;
    state.prevAnchor = null;
  }

  function setVolume(name, value) {
    state.volumes[name] = value;
    if (state.buses) state.buses[name].gain.setTargetAtTime(value, state.ctx.currentTime, 0.02);
  }

  function setTimeline(tl) {
    if (state.playing) pause();
    state.tl = tl;
    state.pausedQ = 0;
    state.loop = null;
  }

  K.audio = {
    play,
    pause,
    seek,
    position,
    setTempo,
    setVolume,
    setTimeline,
    setTranspose: (n) => {
      state.transpose = n;
    },
    setLoop: (range) => {
      state.loop = range;
    },
    onEnd: (fn) => {
      state.onEnd = fn;
    },
    isPlaying: () => state.playing,
    tempo: () => state.qpm,
  };

  K.debug = {
    position,
    counts,
    gains: () => Object.assign({}, state.volumes),
    cursors: () => Object.assign({}, state.cursors),
    contextState: () => (state.ctx ? state.ctx.state : "none"),
  };
})();
