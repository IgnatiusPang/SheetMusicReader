/**
 * Node.js Runtime Test Harness for docs/sheet_music_engine.wasm
 * Tests WebAssembly exports and validates against GeneralKeen Lean 4 oracles.
 */

const fs = require('fs');
const path = require('path');
const assert = require('assert');

async function runWasmTests() {
  console.log('=== Testing docs/sheet_music_engine.wasm Runtime Execution ===');

  const wasmPath = path.join(__dirname, '../docs/sheet_music_engine.wasm');
  const wasmBytes = fs.readFileSync(wasmPath);
  console.log(`Loaded WASM Binary: ${wasmBytes.length} bytes (${(wasmBytes.length / 1024).toFixed(1)} KB)`);

  const { instance } = await WebAssembly.instantiate(wasmBytes, { env: {} });
  const exports = instance.exports;
  const memory = exports.memory;

  // 1. Verify Memory Allocation & Deallocation
  console.log('\n[Test 1] Memory Lifecycle (wasm_alloc / wasm_dealloc)...');
  const testLen = 1024;
  const ptr = exports.wasm_alloc(testLen);
  assert(ptr > 0, 'wasm_alloc returned null pointer');
  const buf = new Uint8Array(memory.buffer, ptr, testLen);
  buf[0] = 0xAA;
  buf[testLen - 1] = 0x55;
  assert.strictEqual(buf[0], 0xAA);
  assert.strictEqual(buf[testLen - 1], 0x55);
  exports.wasm_dealloc(ptr, testLen);
  console.log('✓ wasm_alloc and wasm_dealloc passed.');

  // 2. Verify GeneralKeen Lean 4 Lifted Oracles: Diatonic to MIDI
  console.log('\n[Test 2] Diatonic to MIDI (GeneralKeen Lean 4 Oracles)...');
  assert.strictEqual(exports.wasm_diatonic_to_midi(28, 0), 60, 'Oracle 1: C4');
  assert.strictEqual(exports.wasm_diatonic_to_midi(30, 0), 64, 'Oracle 2: E4');
  assert.strictEqual(exports.wasm_diatonic_to_midi(31, 1), 66, 'Oracle 3: F#4');
  assert.strictEqual(exports.wasm_diatonic_to_midi(18, 0), 43, 'Oracle 5: G2');
  console.log('✓ All 4 Lean 4 unit test oracles matched exactly.');

  // 3. Verify Key Alteration Oracles (Circle of Fifths)
  console.log('\n[Test 3] Key Alteration Circle of Fifths (GeneralKeen Oracles)...');
  assert.strictEqual(exports.wasm_key_alter(2, 3), 1, 'Key 2# step F -> sharp');
  assert.strictEqual(exports.wasm_key_alter(2, 0), 1, 'Key 2# step C -> sharp');
  assert.strictEqual(exports.wasm_key_alter(2, 4), 0, 'Key 2# step G -> natural');
  console.log('✓ Key alteration rules passed.');

  // 4. Verify Score to LilyPond (.ly) WASM Generation
  console.log('\n[Test 4] Score to LilyPond Serialization...');
  const sampleScore = {
    title: "Charles Dancla - Cantabile Op. 130",
    bpm: 80,
    program: 40,
    measures: [
      {
        time: [4, 4], key: 2, clef: "treble",
        events: [
          { x: 10, value: 2.0, is_rest: false, stem: 1, tie: false, midis: [64] },
          { x: 30, value: 1.0, is_rest: false, stem: 1, tie: false, midis: [66] },
          { x: 50, value: 1.0, is_rest: false, stem: 1, tie: false, midis: [67] }
        ]
      }
    ]
  };

  const jsonStr = JSON.stringify(sampleScore);
  const jsonBytes = Buffer.from(jsonStr);
  const inPtr = exports.wasm_alloc(jsonBytes.length);
  new Uint8Array(memory.buffer, inPtr, jsonBytes.length).set(jsonBytes);

  const outLenPtr = exports.wasm_alloc(4);
  const outPtr = exports.wasm_score_to_lilypond(inPtr, jsonBytes.length, outLenPtr);

  const outLen = new DataView(memory.buffer, outLenPtr, 4).getUint32(0, true);
  const lyBytes = new Uint8Array(memory.buffer, outPtr, outLen);
  const lyText = new TextDecoder().decode(lyBytes);

  assert(lyText.includes('\\version "2.26.0"'), 'Missing LilyPond version');
  assert(lyText.includes('Charles Dancla - Cantabile Op. 130'), 'Missing title');
  assert(lyText.includes('\\key d \\major'), 'Missing key signature');
  console.log('✓ LilyPond score generated cleanly (length=' + outLen + ' bytes).');

  // 5. Verify Score to Standard MIDI Binary File
  console.log('\n[Test 5] Score to Standard MIDI File (SMF Type 0)...');
  const midiOutLenPtr = exports.wasm_alloc(4);
  const midiOutPtr = exports.wasm_score_to_midi(inPtr, jsonBytes.length, midiOutLenPtr);

  const midiLen = new DataView(memory.buffer, midiOutLenPtr, 4).getUint32(0, true);
  const midiBytes = new Uint8Array(memory.buffer, midiOutPtr, midiLen);

  assert(midiLen >= 22, 'MIDI file too small');
  const header = String.fromCharCode(...midiBytes.slice(0, 4));
  assert.strictEqual(header, 'MThd', 'Invalid MIDI header');
  const track = String.fromCharCode(...midiBytes.slice(14, 18));
  assert.strictEqual(track, 'MTrk', 'Invalid MIDI track header');
  console.log('✓ Valid Type 0 MIDI binary generated (length=' + midiLen + ' bytes).');

  // Clean up
  exports.wasm_dealloc(inPtr, jsonBytes.length);
  exports.wasm_dealloc(outLenPtr, 4);
  exports.wasm_dealloc(outPtr, outLen);
  exports.wasm_dealloc(midiOutLenPtr, 4);
  exports.wasm_dealloc(midiOutPtr, midiLen);

  // 6. Verify wasm_detect_systems
  console.log('\n[Test 6] Staff System Detection (wasm_detect_systems)...');
  const rowCount = 200;
  const densities = new Float32Array(rowCount);
  // Add 5 peaks at y = 60, 72, 84, 96, 108 with spacing 12
  [60, 72, 84, 96, 108].forEach(y => { densities[y] = 0.8; });
  const densByteLen = rowCount * 4;
  const densPtr = exports.wasm_alloc(densByteLen);
  new Float32Array(memory.buffer, densPtr, rowCount).set(densities);

  const sysOutLenPtr = exports.wasm_alloc(4);
  const sysOutPtr = exports.wasm_detect_systems(densPtr, rowCount, 0.25, 800.0, sysOutLenPtr);
  const sysLen = new DataView(memory.buffer, sysOutLenPtr, 4).getUint32(0, true);
  const sysJson = new TextDecoder().decode(new Uint8Array(memory.buffer, sysOutPtr, sysLen));
  const detectedSys = JSON.parse(sysJson);

  assert(Array.isArray(detectedSys), 'Expected array of staff systems');
  assert(detectedSys.length >= 1, 'Expected at least 1 staff system detected');
  assert.strictEqual(detectedSys[0].lines.length, 5, 'System should have 5 lines');
  console.log(`✓ Staff systems detected successfully (${detectedSys.length} system found).`);

  exports.wasm_dealloc(densPtr, densByteLen);
  exports.wasm_dealloc(sysOutLenPtr, 4);
  exports.wasm_dealloc(sysOutPtr, sysLen);

  // 7. Verify wasm_repair_measure
  console.log('\n[Test 7] Measure Rhythm Repair (wasm_repair_measure)...');
  const testEvents = [
    { x: 10, value: 1.0, is_rest: false, stem: 1, tie: false, midis: [60] },
    { x: 30, value: 1.0, is_rest: false, stem: 1, tie: false, midis: [62] },
    { x: 50, value: 1.0, is_rest: false, stem: 1, tie: false, midis: [64] }
  ];
  const evStr = JSON.stringify(testEvents);
  const evBytes = Buffer.from(evStr);
  const evPtr = exports.wasm_alloc(evBytes.length);
  new Uint8Array(memory.buffer, evPtr, evBytes.length).set(evBytes);

  const repOutLenPtr = exports.wasm_alloc(4);
  const repOutPtr = exports.wasm_repair_measure(evPtr, evBytes.length, 4.0, repOutLenPtr);
  const repLen = new DataView(memory.buffer, repOutLenPtr, 4).getUint32(0, true);
  const repJson = new TextDecoder().decode(new Uint8Array(memory.buffer, repOutPtr, repLen));
  const repairedEv = JSON.parse(repJson);

  assert(Array.isArray(repairedEv), 'Repaired events should be an array');
  assert(repairedEv.length >= 3, 'Repaired events preserved notes');
  console.log(`✓ wasm_repair_measure validated (${repairedEv.length} events).`);

  exports.wasm_dealloc(evPtr, evBytes.length);
  exports.wasm_dealloc(repOutLenPtr, 4);
  exports.wasm_dealloc(repOutPtr, repLen);

  // 8. Verify wasm_canonical_clef
  console.log('\n[Test 8] Canonical Clef Resolution (wasm_canonical_clef)...');
  const clefTests = [
    { input: 'french', expected: 'treble' },
    { input: 'subbass', expected: 'bass' },
    { input: 'soprano', expected: 'alto' },
    { input: 'tenor', expected: 'tenor' },
    { input: 'percussion', expected: 'percussion' },
    { input: 'G8vb', expected: 'treble' },
    { input: 'unknown_clef_token', expected: 'treble' }
  ];
  for (const { input, expected } of clefTests) {
    const cBytes = Buffer.from(input);
    const cPtr = exports.wasm_alloc(cBytes.length);
    new Uint8Array(memory.buffer, cPtr, cBytes.length).set(cBytes);
    const cOutLenPtr = exports.wasm_alloc(4);
    const cOutPtr = exports.wasm_canonical_clef(cPtr, cBytes.length, cOutLenPtr);
    const cLen = new DataView(memory.buffer, cOutLenPtr, 4).getUint32(0, true);
    const canon = new TextDecoder().decode(new Uint8Array(memory.buffer, cOutPtr, cLen));
    assert.strictEqual(canon, expected, `Clef ${input} -> expected ${expected}, got ${canon}`);
    exports.wasm_dealloc(cPtr, cBytes.length);
    exports.wasm_dealloc(cOutLenPtr, 4);
    exports.wasm_dealloc(cOutPtr, cLen);
  }
  console.log('✓ All canonical clef mappings resolved successfully.');

  // 9. Verify wasm_restore_silent_rests (Rule 3.7)
  console.log('\n[Test 9] Silent Rest Restoration (wasm_restore_silent_rests - Rule 3.7)...');
  const underfullEvents = [
    { x: 10, value: 2.0, is_rest: false, stem: 1, tie: false, midis: [60] }
  ];
  const uStr = JSON.stringify(underfullEvents);
  const uBytes = Buffer.from(uStr);
  const uPtr = exports.wasm_alloc(uBytes.length);
  new Uint8Array(memory.buffer, uPtr, uBytes.length).set(uBytes);
  const restOutLenPtr = exports.wasm_alloc(4);
  const restOutPtr = exports.wasm_restore_silent_rests(uPtr, uBytes.length, 4.0, restOutLenPtr);
  const restLen = new DataView(memory.buffer, restOutLenPtr, 4).getUint32(0, true);
  const restored = JSON.parse(new TextDecoder().decode(new Uint8Array(memory.buffer, restOutPtr, restLen)));
  assert.strictEqual(restored.length, 2, 'Should add 1 rest');
  assert.strictEqual(restored[1].is_rest, true, 'Second event must be a rest');
  assert.strictEqual(restored[1].value, 2.0, 'Rest should be 2.0 beats');
  exports.wasm_dealloc(uPtr, uBytes.length);
  exports.wasm_dealloc(restOutLenPtr, 4);
  exports.wasm_dealloc(restOutPtr, restLen);
  console.log('✓ Duration deficit restored with standard silent rest.');

  // 10. Verify wasm_apply_stem_beaming (Rule 3.8)
  console.log('\n[Test 10] Stem Beaming (wasm_apply_stem_beaming - Rule 3.8)...');
  const shortNotes = [
    { x: 10, value: 0.5, is_rest: false, stem: 1, tie: false, midis: [60] },
    { x: 20, value: 0.5, is_rest: false, stem: 1, tie: false, midis: [62] },
    { x: 30, value: 1.0, is_rest: false, stem: 1, tie: false, midis: [64] }
  ];
  const snStr = JSON.stringify(shortNotes);
  const snBytes = Buffer.from(snStr);
  const snPtr = exports.wasm_alloc(snBytes.length);
  new Uint8Array(memory.buffer, snPtr, snBytes.length).set(snBytes);
  const beamOutLenPtr = exports.wasm_alloc(4);
  const beamOutPtr = exports.wasm_apply_stem_beaming(snPtr, snBytes.length, beamOutLenPtr);
  const beamLen = new DataView(memory.buffer, beamOutLenPtr, 4).getUint32(0, true);
  const beamed = JSON.parse(new TextDecoder().decode(new Uint8Array(memory.buffer, beamOutPtr, beamLen)));
  assert.strictEqual(beamed[0].beam, '[', 'First eighth note should have beam start [');
  assert.strictEqual(beamed[1].beam, ']', 'Second eighth note should have beam end ]');
  assert.strictEqual(beamed[2].beam, null, 'Quarter note should not be beamed');
  exports.wasm_dealloc(snPtr, snBytes.length);
  exports.wasm_dealloc(beamOutLenPtr, 4);
  exports.wasm_dealloc(beamOutPtr, beamLen);
  console.log('✓ Consecutive short notes automatically beamed.');

  // 11. Verify Polyphonic Score Serialization in LilyPond
  console.log('\n[Test 11] Polyphonic Voice Serialization (<< { v1 } \\\\ { v2 } >>)...');
  const polyScore = {
    title: "Polyphonic Voice Benchmark",
    bpm: 90,
    program: 0,
    measures: [
      {
        time: [4, 4], key: 0, clef: "treble",
        events: [],
        voices: [
          [
            { x: 10, value: 2.0, is_rest: false, stem: 1, tie: false, midis: [67] },
            { x: 30, value: 2.0, is_rest: false, stem: 1, tie: false, midis: [69] }
          ],
          [
            { x: 10, value: 4.0, is_rest: false, stem: -1, tie: false, midis: [60] }
          ]
        ]
      }
    ]
  };
  const polyStr = JSON.stringify(polyScore);
  const polyBytes = Buffer.from(polyStr);
  const polyInPtr = exports.wasm_alloc(polyBytes.length);
  new Uint8Array(memory.buffer, polyInPtr, polyBytes.length).set(polyBytes);
  const polyOutLenPtr = exports.wasm_alloc(4);
  const polyOutPtr = exports.wasm_score_to_lilypond(polyInPtr, polyBytes.length, polyOutLenPtr);
  const polyOutLen = new DataView(memory.buffer, polyOutLenPtr, 4).getUint32(0, true);
  const polyLy = new TextDecoder().decode(new Uint8Array(memory.buffer, polyOutPtr, polyOutLen));
  assert(polyLy.includes('<< {'), 'LilyPond output must contain << { polyphonic start');
  assert(polyLy.includes('\\\\'), 'LilyPond output must contain \\\\ voice separator');
  assert(polyLy.includes('g\'2 a\'2'), 'Voice 1 events present');
  assert(polyLy.includes('c\'1'), 'Voice 2 events present');
  exports.wasm_dealloc(polyInPtr, polyBytes.length);
  exports.wasm_dealloc(polyOutLenPtr, 4);
  exports.wasm_dealloc(polyOutPtr, polyOutLen);
  console.log('✓ Polyphonic voices serialized correctly into standard LilyPond syntax.');

  console.log('\n======================================================');
  console.log('ALL WASM RUNTIME SUITE TESTS PASSED CLEANLY (100%)');
  console.log('======================================================');
}

runWasmTests().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});

// <!-- APAF Bioinformatics | test_wasm_runtime.js | Approved | 2026-10-28 -->

