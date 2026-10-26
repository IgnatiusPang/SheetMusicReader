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

  console.log('\n======================================================');
  console.log('ALL WASM RUNTIME SUITE TESTS PASSED CLEANLY (100%)');
  console.log('======================================================');
}

runWasmTests().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
