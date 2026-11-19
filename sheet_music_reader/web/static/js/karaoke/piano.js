/* Small keyboard strip: shows the note being sung and the chord underneath it. */
(function () {
  "use strict";
  const K = (window.Karaoke = window.Karaoke || {});
  const LOW = 48; // C3
  const HIGH = 84; // C6
  const BLACK = new Set([1, 3, 6, 8, 10]);
  const NAMES = ["C", "C♯", "D", "E♭", "E", "F", "F♯", "G", "A♭", "A", "B♭", "B"];
  const keys = new Map();
  let lit = [];

  const isBlack = (midi) => BLACK.has(((midi % 12) + 12) % 12);
  const noteName = (midi) => NAMES[((midi % 12) + 12) % 12] + (Math.floor(midi / 12) - 1);

  function init(el) {
    el.textContent = "";
    keys.clear();
    const whites = K.timeline.range(HIGH - LOW + 1).map((i) => LOW + i).filter((m) => !isBlack(m));
    whites.forEach((midi, i) => {
      const key = document.createElement("div");
      key.className = "key white";
      key.style.left = (i * 100) / whites.length + "%";
      key.style.width = 100 / whites.length + "%";
      if (midi % 12 === 0) key.innerHTML = "<span>" + noteName(midi) + "</span>";
      el.appendChild(key);
      keys.set(midi, key);
      if (midi + 1 <= HIGH && isBlack(midi + 1)) {
        const black = document.createElement("div");
        black.className = "key black";
        black.style.left = ((i + 1) * 100) / whites.length + "%";
        black.style.width = 62 / whites.length + "%";
        el.appendChild(black);
        keys.set(midi + 1, black);
      }
    });
  }

  function fold(midi) {
    return midi < LOW ? fold(midi + 12) : midi > HIGH ? fold(midi - 12) : midi;
  }

  function show(melodyMidi, chordMidis) {
    lit.forEach((k) => k.classList.remove("sing", "chord"));
    const chordKeys = (chordMidis || []).map((m) => keys.get(fold(m))).filter(Boolean);
    chordKeys.forEach((k) => k.classList.add("chord"));
    const sing = melodyMidi == null ? null : keys.get(fold(melodyMidi));
    if (sing) sing.classList.add("sing");
    lit = chordKeys.concat(sing ? [sing] : []);
  }

  K.piano = { init, show, noteName };
})();
