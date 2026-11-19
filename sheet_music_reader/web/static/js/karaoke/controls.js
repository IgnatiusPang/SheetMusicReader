/* Karaoke controls: wires the page to the timeline, audio engine and stage. */
(function () {
  "use strict";
  const K = (window.Karaoke = window.Karaoke || {});
  const $ = (id) => document.getElementById(id);
  const boot = window.KARAOKE_BOOT || { apiMode: false, data: null };

  const app = {
    score: null,
    tl: null,
    modeId: null,
    speed: 1,
    transpose: 0,
    lastKey: "",
    lastPhrase: -1,
    lastBeat: -1,
    listed: [],
  };

  /* ---------- small helpers ---------- */

  function notice(text) {
    const el = $("notice");
    el.hidden = !text;
    el.textContent = text || "";
  }

  function phraseText(phrase) {
    return phrase.words.reduce((line, w) => (line.endsWith("-") ? line.slice(0, -1) + w.text : (line ? line + " " : "") + w.text), "");
  }

  function fetchJson(url, options) {
    return fetch(url, options).then((res) =>
      res.json().then((body) => {
        if (!res.ok) throw new Error(body.error || "Request failed (" + res.status + ")");
        return body;
      })
    );
  }

  const currentPhrase = () => app.tl.phraseAt(Math.max(0, K.audio.position()));

  /* ---------- rendering of static parts ---------- */

  function renderModeTabs() {
    const nav = $("modeTabs");
    nav.textContent = "";
    nav.hidden = app.score.modes.length < 2;
    app.score.modes.forEach((mode) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "tab";
      b.textContent = mode.label || mode.mode_id;
      b.dataset.mode = mode.mode_id;
      b.setAttribute("data-testid", "mode-" + mode.mode_id);
      b.setAttribute("aria-pressed", String(mode.mode_id === app.modeId));
      b.addEventListener("click", () => selectMode(mode.mode_id));
      nav.appendChild(b);
    });
  }

  function renderPhraseList() {
    const list = $("phraseList");
    list.textContent = "";
    app.tl.phrases.forEach((p) => {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.className = "phrase-btn";
      b.dataset.phrase = p.order;
      const label = document.createElement("span");
      label.className = "phrase-section";
      label.textContent = p.section_label || "";
      const text = document.createElement("span");
      text.className = "phrase-text";
      text.textContent = phraseText(p) || "(instrumental)";
      b.append(label, text);
      b.addEventListener("click", () => seekTo(p.start_q));
      li.appendChild(b);
      list.appendChild(li);
    });
  }

  function renderBeatDots() {
    const el = $("beatDots");
    el.textContent = "";
    K.timeline.range(app.tl.beatsPerBar).forEach(() => el.appendChild(document.createElement("i")));
  }

  function showTempo() {
    const qpm = K.audio.tempo();
    $("tempoSlider").value = Math.round(qpm);
    $("tempoOut").textContent = Math.round(app.speed * 100) + "% · " + Math.round(qpm) + " bpm";
    Array.from(document.querySelectorAll(".chip[data-speed]")).forEach((chip) =>
      chip.setAttribute("aria-pressed", String(Math.abs(Number(chip.dataset.speed) - app.speed) < 0.01))
    );
  }

  function showTranspose() {
    const n = app.transpose;
    $("transposeOut").textContent = n === 0 ? "As written" : (n > 0 ? "+" : "−") + Math.abs(n) + " semitone" + (Math.abs(n) === 1 ? "" : "s");
  }

  function showPlayState() {
    const playing = K.audio.isPlaying();
    $("playBtn").setAttribute("aria-pressed", String(playing));
    $("playLabel").textContent = playing ? "Pause" : "Play";
    document.body.classList.toggle("is-playing", playing);
    K.stage.setFollow(playing);
  }

  /* ---------- per-frame drawing ---------- */

  function frame() {
    window.requestAnimationFrame(frame);
    if (!app.tl) return;
    const real = K.audio.position();
    const countingIn = K.audio.isPlaying() && real < startedFrom - 1e-6;
    const q = countingIn ? startedFrom : real; // hold the picture still while the count-in clicks
    const now = K.stage.update(q);
    if (!now) return;
    K.debug.rendered = { q: Math.max(0, q), ev: now.event ? now.event.event_index : null, word: now.word ? now.word.order : null, phrase: now.phrase.order };
    const tl = app.tl;
    const pos = Math.max(0, q);
    const chord = tl.chordAt(pos);
    const ev = now.event;
    const key = (ev ? ev.order : -1) + "|" + (chord ? chord.onset_q : -1) + "|" + app.transpose;

    if (key !== app.lastKey) {
      app.lastKey = key;
      const isNote = ev && ev.kind === "N" && ev.midi != null;
      $("nowNote").textContent = isNote ? K.piano.noteName(ev.midi + app.transpose) : ev ? "rest" : "–";
      $("nowWord").textContent = now.word ? now.word.text : "";
      $("nowChord").textContent = chord ? chord.symbol : "–";
      K.piano.show(isNote ? ev.midi + app.transpose : null, chord ? chord.chord_midis.map((m) => m + app.transpose) : []);
    }

    if (now.phrase.order !== app.lastPhrase) {
      app.lastPhrase = now.phrase.order;
      const next = tl.phrases[now.phrase.order + 1];
      $("sectionLabel").textContent = (now.phrase.section_label || "") + " · line " + (now.phrase.order + 1) + " of " + tl.phrases.length;
      $("nextLine").textContent = next ? "Next: " + (phraseText(next) || "(instrumental)") : "Last line.";
      Array.from(document.querySelectorAll(".phrase-btn")).forEach((b) => b.setAttribute("aria-current", String(Number(b.dataset.phrase) === now.phrase.order)));
      if ($("loopToggle").checked) K.audio.setLoop({ start: now.phrase.start_q, end: now.phrase.end_q });
    }

    const bar = tl.barAt(pos);
    const beat = K.audio.isPlaying() && bar ? Math.floor(((((real - bar.start_q) % bar.dur_q) + bar.dur_q) % bar.dur_q) / tl.beatLen + 1e-6) : -1;
    if (beat !== app.lastBeat) {
      app.lastBeat = beat;
      Array.from($("beatDots").children).forEach((dot, i) => dot.classList.toggle("on", i === beat));
    }
    $("status").textContent = K.audio.isPlaying() ? (countingIn ? "Counting in…" : "Playing") : pos > 0 ? "Paused" : "Ready";
  }
  let startedFrom = 0;

  /* ---------- actions ---------- */

  function play() {
    const from = K.audio.position();
    startedFrom = from;
    return K.audio.play({ countIn: $("countInToggle").checked }).then(showPlayState);
  }

  function pause() {
    K.audio.pause();
    showPlayState();
  }

  function seekTo(q) {
    startedFrom = q;
    K.audio.seek(q);
    if ($("loopToggle").checked) {
      const p = app.tl.phraseAt(q);
      K.audio.setLoop({ start: p.start_q, end: p.end_q });
    }
  }

  function stepPhrase(delta) {
    const p = currentPhrase();
    const target = app.tl.phrases[Math.min(app.tl.phrases.length - 1, Math.max(0, p.order + delta))];
    seekTo(target.start_q);
  }

  function setSpeed(speed) {
    app.speed = speed;
    K.audio.setTempo(app.score.tempo_qpm * speed);
    showTempo();
  }

  function selectMode(modeId) {
    const mode = app.score.modes.find((m) => m.mode_id === modeId) || app.score.modes[0];
    app.modeId = mode.mode_id;
    app.tl = K.timeline.build(mode);
    app.lastKey = "";
    app.lastPhrase = -1;
    startedFrom = 0;
    K.audio.setTimeline(app.tl);
    K.stage.setScore(app.score, app.tl);
    $("loopToggle").checked = false;
    $("backingHint").textContent = app.tl.chords.length ? "Bass and chords from the chart." : "This score has no chord symbols, so there is no backing.";
    renderModeTabs();
    renderPhraseList();
    renderBeatDots();
    showPlayState();
  }

  function loadScore(score) {
    if (!score || !score.modes || !score.modes.length) {
      notice("This score has no notes to sing.");
      return;
    }
    notice("");
    app.score = Object.assign({ tempo_qpm: 72, fifths: 0, time_signature: "4/4" }, score);
    app.speed = 1;
    $("songTitle").textContent = score.title || "Untitled";
    document.title = (score.title || "Karaoke") + " · Karaoke Trainer";
    $("songMeta").textContent = [score.composer, score.key, score.time_signature].filter(Boolean).join(" · ");
    K.audio.setTempo(app.score.tempo_qpm);
    selectMode(app.score.modes[0].mode_id);
    showTempo();
  }

  /* ---------- server mode: score list and upload ---------- */

  function fetchScore(id) {
    notice("Reading the score…");
    return fetchJson("/api/karaoke/score/" + encodeURIComponent(id))
      .then(loadScore)
      .catch((err) => notice(err.message));
  }

  function initServerMode() {
    $("serverTools").hidden = false;
    const select = $("scoreSelect");
    select.addEventListener("change", () => select.value && fetchScore(select.value));
    $("pdfUpload").addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const form = new FormData();
      form.append("pdf", file);
      notice("Reading " + file.name + "…");
      fetchJson("/api/karaoke/upload", { method: "POST", body: form })
        .then(loadScore)
        .catch((err) => notice(err.message));
      e.target.value = "";
    });
    return fetchJson("/api/karaoke/list")
      .then((body) => {
        app.listed = body.scores || [];
        app.listed.forEach((s) => {
          const o = document.createElement("option");
          o.value = s.id;
          o.textContent = (s.source_type === "pdf" ? "Chart: " : "Library: ") + s.title;
          select.appendChild(o);
        });
        const wanted = new URLSearchParams(window.location.search).get("score");
        const first = app.listed.find((s) => s.id === wanted) || app.listed[0];
        if (!first) return notice("No scores found. Upload a PDF to begin.");
        select.value = first.id;
        return fetchScore(first.id);
      })
      .catch((err) => notice(err.message));
  }

  /* ---------- wiring ---------- */

  function bindVolume(sliderId, outId, bus) {
    const slider = $(sliderId);
    const apply = () => {
      K.audio.setVolume(bus, Number(slider.value) / 100);
      $(outId).textContent = slider.value + "%";
    };
    slider.addEventListener("input", apply);
    apply();
  }

  function init() {
    K.stage.init($("systems"), seekTo);
    K.piano.init($("keyboard"));
    K.audio.onEnd(() => {
      startedFrom = 0;
      showPlayState();
    });

    $("playBtn").addEventListener("click", () => (K.audio.isPlaying() ? pause() : play()));
    $("restartBtn").addEventListener("click", () => seekTo($("loopToggle").checked ? currentPhrase().start_q : 0));
    $("prevBtn").addEventListener("click", () => stepPhrase(-1));
    $("nextBtn").addEventListener("click", () => stepPhrase(1));
    $("loopToggle").addEventListener("change", (e) => {
      const p = currentPhrase();
      K.audio.setLoop(e.target.checked ? { start: p.start_q, end: p.end_q } : null);
    });
    Array.from(document.querySelectorAll(".chip[data-speed]")).forEach((chip) => chip.addEventListener("click", () => setSpeed(Number(chip.dataset.speed))));
    $("tempoSlider").addEventListener("input", (e) => setSpeed(Number(e.target.value) / app.score.tempo_qpm));
    bindVolume("guideVol", "guideOut", "guide");
    bindVolume("backingVol", "backingOut", "backing");
    bindVolume("clickVol", "clickOut", "click");
    const shift = (delta) => () => {
      app.transpose = Math.max(-6, Math.min(6, app.transpose + delta));
      K.audio.setTranspose(app.transpose);
      showTranspose();
    };
    $("transposeDown").addEventListener("click", shift(-1));
    $("transposeUp").addEventListener("click", shift(1));

    document.addEventListener("keydown", (e) => {
      if (!app.tl || /^(INPUT|SELECT|TEXTAREA|BUTTON|A)$/.test(e.target.tagName)) return;
      if (e.code === "Space") {
        e.preventDefault();
        if (K.audio.isPlaying()) pause();
        else play();
      } else if (e.code === "ArrowRight") stepPhrase(1);
      else if (e.code === "ArrowLeft") stepPhrase(-1);
    });

    let resizeTimer = null;
    window.addEventListener("resize", () => {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(K.stage.relayout, 150);
    });

    window.requestAnimationFrame(frame);
    if (boot.data) loadScore(boot.data);
    if (boot.apiMode) initServerMode();
    else if (!boot.data) notice("No score is embedded in this file.");
  }

  K.app = { state: app, loadScore, selectMode, seekTo };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
