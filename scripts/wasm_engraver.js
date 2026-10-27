/**
 * High-Performance Node.js / WebAssembly Engraving Bridge for SheetMusicReader
 *
 * Invokes docs/sheet_music_engine.wasm to engrave scores to LilyPond and synthesize MIDI.
 *
 * <!-- APAF Bioinformatics | wasm_engraver.js | Approved | 2026-10-28 -->
 */

const fs = require('fs');
const path = require('path');

let wasmInstance = null;

async function getWasmEngine() {
  if (wasmInstance) return wasmInstance;
  const wasmPath = path.resolve(__dirname, '../docs/sheet_music_engine.wasm');
  const wasmBytes = fs.readFileSync(wasmPath);
  const { instance } = await WebAssembly.instantiate(wasmBytes, { env: {} });
  wasmInstance = instance;
  return wasmInstance;
}

function engraveScoreWithWasm(instance, scoreRequest) {
  const exports = instance.exports;
  const memory = exports.memory;

  const jsonStr = typeof scoreRequest === 'string' ? scoreRequest : JSON.stringify(scoreRequest);
  const jsonBytes = Buffer.from(jsonStr);

  // Allocate and copy JSON
  const inPtr = exports.wasm_alloc(jsonBytes.length);
  new Uint8Array(memory.buffer, inPtr, jsonBytes.length).set(jsonBytes);

  // Call wasm_score_to_lilypond
  const lyOutLenPtr = exports.wasm_alloc(4);
  const lyOutPtr = exports.wasm_score_to_lilypond(inPtr, jsonBytes.length, lyOutLenPtr);
  const lyLen = new DataView(memory.buffer, lyOutLenPtr, 4).getUint32(0, true);
  const lyBytes = new Uint8Array(memory.buffer, lyOutPtr, lyLen);
  const lilypondText = new TextDecoder().decode(lyBytes);

  // Call wasm_score_to_midi
  const midiOutLenPtr = exports.wasm_alloc(4);
  const midiOutPtr = exports.wasm_score_to_midi(inPtr, jsonBytes.length, midiOutLenPtr);
  const midiLen = new DataView(memory.buffer, midiOutLenPtr, 4).getUint32(0, true);
  const midiBytes = Buffer.from(new Uint8Array(memory.buffer, midiOutPtr, midiLen));

  // Deallocate
  exports.wasm_dealloc(inPtr, jsonBytes.length);
  exports.wasm_dealloc(lyOutLenPtr, 4);
  exports.wasm_dealloc(lyOutPtr, lyLen);
  exports.wasm_dealloc(midiOutLenPtr, 4);
  exports.wasm_dealloc(midiOutPtr, midiLen);

  return { lilypond: lilypondText, midi: midiBytes };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes('--help')) {
    console.log('Usage: node scripts/wasm_engraver.js --score <score.json> [--out-ly <file.ly>] [--out-midi <file.midi>]');
    console.log('       node scripts/wasm_engraver.js --batch <batch_manifest.json>');
    process.exit(0);
  }

  const engine = await getWasmEngine();

  if (args.includes('--batch')) {
    const batchIdx = args.indexOf('--batch') + 1;
    const batchPath = args[batchIdx];
    const manifest = JSON.parse(fs.readFileSync(batchPath, 'utf-8'));
    console.log(`Processing batch of ${manifest.length} scores with sheet_music_engine.wasm...`);
    const t0 = Date.now();
    let successCount = 0;
    for (const item of manifest) {
      try {
        const scoreReq = item.score ? item.score : JSON.parse(fs.readFileSync(item.score_json_path, 'utf-8'));
        const { lilypond, midi } = engraveScoreWithWasm(engine, scoreReq);
        if (item.out_ly) {
          fs.mkdirSync(path.dirname(item.out_ly), { recursive: true });
          fs.writeFileSync(item.out_ly, lilypond, 'utf-8');
        }
        if (item.out_midi) {
          fs.mkdirSync(path.dirname(item.out_midi), { recursive: true });
          fs.writeFileSync(item.out_midi, midi);
        }
        successCount++;
      } catch (err) {
        console.error(`Error processing ${item.name || item.out_ly}:`, err.message);
      }
    }
    const elapsed = Date.now() - t0;
    console.log(`WASM Batch Completed: ${successCount}/${manifest.length} scores in ${elapsed}ms (${(elapsed / manifest.length).toFixed(2)} ms/score).`);
    return;
  }

  const scoreIdx = args.indexOf('--score') + 1;
  const scorePath = args[scoreIdx];
  const jsonContent = scorePath === '-' ? fs.readFileSync(0, 'utf-8') : fs.readFileSync(scorePath, 'utf-8');
  const scoreReq = JSON.parse(jsonContent);

  const { lilypond, midi } = engraveScoreWithWasm(engine, scoreReq);

  const lyIdx = args.indexOf('--out-ly');
  if (lyIdx !== -1) {
    const lyPath = args[lyIdx + 1];
    fs.mkdirSync(path.dirname(lyPath), { recursive: true });
    fs.writeFileSync(lyPath, lilypond, 'utf-8');
  } else {
    console.log(lilypond);
  }

  const midiIdx = args.indexOf('--out-midi');
  if (midiIdx !== -1) {
    const midiPath = args[midiIdx + 1];
    fs.mkdirSync(path.dirname(midiPath), { recursive: true });
    fs.writeFileSync(midiPath, midi);
  }
}

if (require.main === module) {
  main().catch(err => {
    console.error('Fatal WASM Engraver Error:', err);
    process.exit(1);
  });
}

module.exports = { getWasmEngine, engraveScoreWithWasm };
