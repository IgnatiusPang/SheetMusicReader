//! WebAssembly C-compatible ABI exports for sheet_music_engine.
//! Zero-cost memory buffer transfers between JavaScript and WASM.

use crate::lilypond::{generate_multistaff_score_document, generate_score_document, Measure};
use crate::midi::generate_midi;
use crate::omr::detect_staff_systems_from_densities;
use crate::rhythm::{repair_measure, NoteEvent};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct ScoreRequest {
    pub title: Option<String>,
    pub bpm: Option<u32>,
    pub program: Option<u8>,
    #[serde(default)]
    pub measures: Vec<Measure>,
    #[serde(default)]
    pub staves: Option<Vec<Vec<Measure>>>,
}

#[derive(Debug, Serialize)]
pub struct ProcessedScoreResponse {
    pub title: String,
    pub lilypond: String,
    pub midi_base64: String,
    pub measure_count: usize,
    pub total_notes: usize,
}

/// Allocates a byte buffer of `len` bytes in WASM linear memory.
#[no_mangle]
pub extern "C" fn wasm_alloc(len: usize) -> *mut u8 {
    let mut buf = Vec::with_capacity(len.max(1));
    let ptr = buf.as_mut_ptr();
    std::mem::forget(buf);
    ptr
}

/// Deallocates a byte buffer of `len` bytes previously allocated by `wasm_alloc`.
///
/// # Safety
/// Caller must ensure `ptr` was allocated by `wasm_alloc` and `len` matches allocated size.
#[no_mangle]
pub unsafe extern "C" fn wasm_dealloc(ptr: *mut u8, len: usize) {
    if !ptr.is_null() && len > 0 {
        let _ = Vec::from_raw_parts(ptr, 0, len);
    }
}

/// Helper to serialize a byte slice or string into WASM memory and return pointer + length.
fn allocate_output_bytes(bytes: &[u8], out_len_ptr: *mut usize) -> *mut u8 {
    let len = bytes.len();
    if !out_len_ptr.is_null() {
        unsafe {
            *out_len_ptr = len;
        }
    }
    let ptr = wasm_alloc(len);
    if !ptr.is_null() && len > 0 {
        unsafe {
            std::ptr::copy_nonoverlapping(bytes.as_ptr(), ptr, len);
        }
    }
    ptr
}

/// Converts score JSON into LilyPond score (.ly string).
///
/// # Safety
/// Caller must provide a valid `json_ptr` of length `json_len` and valid `out_len_ptr`.
#[no_mangle]
pub unsafe extern "C" fn wasm_score_to_lilypond(
    json_ptr: *const u8,
    json_len: usize,
    out_len_ptr: *mut usize,
) -> *mut u8 {
    if json_ptr.is_null() || json_len == 0 {
        return allocate_output_bytes(b"", out_len_ptr);
    }

    let slice = std::slice::from_raw_parts(json_ptr, json_len);
    let req: ScoreRequest = match serde_json::from_slice(slice) {
        Ok(r) => r,
        Err(e) => {
            let err_msg = format!("% JSON Error: {}", e);
            return allocate_output_bytes(err_msg.as_bytes(), out_len_ptr);
        }
    };

    let title = req.title.as_deref().unwrap_or("Dancla - Cantabile Op. 130");
    let ly = if let Some(staves) = &req.staves {
        if staves.len() > 1 {
            generate_multistaff_score_document(title, staves)
        } else if let Some(first) = staves.first() {
            generate_score_document(title, first)
        } else {
            generate_score_document(title, &req.measures)
        }
    } else {
        generate_score_document(title, &req.measures)
    };
    allocate_output_bytes(ly.as_bytes(), out_len_ptr)
}

/// Converts score JSON directly into Standard MIDI binary (.mid bytes).
///
/// # Safety
/// Caller must provide a valid `json_ptr` of length `json_len` and valid `out_len_ptr`.
#[no_mangle]
pub unsafe extern "C" fn wasm_score_to_midi(
    json_ptr: *const u8,
    json_len: usize,
    out_len_ptr: *mut usize,
) -> *mut u8 {
    if json_ptr.is_null() || json_len == 0 {
        return allocate_output_bytes(&[], out_len_ptr);
    }

    let slice = std::slice::from_raw_parts(json_ptr, json_len);
    let req: ScoreRequest = match serde_json::from_slice(slice) {
        Ok(r) => r,
        Err(_) => return allocate_output_bytes(&[], out_len_ptr),
    };

    let mut all_events = Vec::new();
    let measures_ref = if let Some(staves) = &req.staves {
        if let Some(first) = staves.first() {
            first.as_slice()
        } else {
            &req.measures[..]
        }
    } else {
        &req.measures[..]
    };
    for m in measures_ref {
        if !m.events.is_empty() {
            all_events.extend(m.events.clone());
        } else if let Some(voices) = &m.voices {
            if let Some(v0) = voices.first() {
                all_events.extend(v0.clone());
            }
        }
    }

    let bpm = req.bpm.unwrap_or(80);
    let program = req.program.unwrap_or(40); // Violin default
    let midi_bytes = generate_midi(&all_events, bpm, program);
    allocate_output_bytes(&midi_bytes, out_len_ptr)
}

/// Runs staff system detection on a row density array from canvas image scan.
///
/// # Safety
/// Caller must provide a valid `densities_ptr` of length `count` and valid `out_len_ptr`.
#[no_mangle]
pub unsafe extern "C" fn wasm_detect_systems(
    densities_ptr: *const f32,
    count: usize,
    min_density: f32,
    width: f32,
    out_len_ptr: *mut usize,
) -> *mut u8 {
    if densities_ptr.is_null() || count < 5 {
        return allocate_output_bytes(b"[]", out_len_ptr);
    }

    let slice = std::slice::from_raw_parts(densities_ptr, count);
    let systems = detect_staff_systems_from_densities(slice, min_density, width);
    let json = serde_json::to_string(&systems).unwrap_or_else(|_| "[]".to_string());
    allocate_output_bytes(json.as_bytes(), out_len_ptr)
}

/// Repairs an overfull or underfull measure JSON.
///
/// # Safety
/// Caller must provide a valid `events_json_ptr` of length `events_json_len` and valid `out_len_ptr`.
#[no_mangle]
pub unsafe extern "C" fn wasm_repair_measure(
    events_json_ptr: *const u8,
    events_json_len: usize,
    expected: f64,
    out_len_ptr: *mut usize,
) -> *mut u8 {
    if events_json_ptr.is_null() || events_json_len == 0 {
        return allocate_output_bytes(b"[]", out_len_ptr);
    }

    let slice = std::slice::from_raw_parts(events_json_ptr, events_json_len);
    let events: Vec<NoteEvent> = match serde_json::from_slice(slice) {
        Ok(ev) => ev,
        Err(_) => return allocate_output_bytes(b"[]", out_len_ptr),
    };

    let repaired = repair_measure(&events, expected);
    let json = serde_json::to_string(&repaired).unwrap_or_else(|_| "[]".to_string());
    allocate_output_bytes(json.as_bytes(), out_len_ptr)
}

/// Workspace Rule 3.7: Pads a measure with duration deficits using standard silent rests.
///
/// # Safety
/// Caller must provide a valid `events_json_ptr` of length `events_json_len` and valid `out_len_ptr`.
#[no_mangle]
pub unsafe extern "C" fn wasm_restore_silent_rests(
    events_json_ptr: *const u8,
    events_json_len: usize,
    expected: f64,
    out_len_ptr: *mut usize,
) -> *mut u8 {
    if events_json_ptr.is_null() || events_json_len == 0 {
        return allocate_output_bytes(b"[]", out_len_ptr);
    }

    let slice = std::slice::from_raw_parts(events_json_ptr, events_json_len);
    let events: Vec<NoteEvent> = match serde_json::from_slice(slice) {
        Ok(ev) => ev,
        Err(_) => return allocate_output_bytes(b"[]", out_len_ptr),
    };

    let restored = crate::rhythm::restore_silent_rests(&events, expected);
    let json = serde_json::to_string(&restored).unwrap_or_else(|_| "[]".to_string());
    allocate_output_bytes(json.as_bytes(), out_len_ptr)
}

/// Workspace Rule 3.8: Automatically beams consecutive short notes (<= 0.5b).
///
/// # Safety
/// Caller must provide a valid `events_json_ptr` of length `events_json_len` and valid `out_len_ptr`.
#[no_mangle]
pub unsafe extern "C" fn wasm_apply_stem_beaming(
    events_json_ptr: *const u8,
    events_json_len: usize,
    out_len_ptr: *mut usize,
) -> *mut u8 {
    if events_json_ptr.is_null() || events_json_len == 0 {
        return allocate_output_bytes(b"[]", out_len_ptr);
    }

    let slice = std::slice::from_raw_parts(events_json_ptr, events_json_len);
    let events: Vec<NoteEvent> = match serde_json::from_slice(slice) {
        Ok(ev) => ev,
        Err(_) => return allocate_output_bytes(b"[]", out_len_ptr),
    };

    let beamed = crate::rhythm::apply_stem_beaming(&events);
    let json = serde_json::to_string(&beamed).unwrap_or_else(|_| "[]".to_string());
    allocate_output_bytes(json.as_bytes(), out_len_ptr)
}

/// Resolves a clef token to its canonical notation family (treble, bass, alto, tenor, percussion).
///
/// # Safety
/// Caller must provide a valid `clef_ptr` of length `clef_len` and valid `out_len_ptr`.
#[no_mangle]
pub unsafe extern "C" fn wasm_canonical_clef(
    clef_ptr: *const u8,
    clef_len: usize,
    out_len_ptr: *mut usize,
) -> *mut u8 {
    if clef_ptr.is_null() || clef_len == 0 {
        return allocate_output_bytes(b"treble", out_len_ptr);
    }
    let slice = std::slice::from_raw_parts(clef_ptr, clef_len);
    let s = std::str::from_utf8(slice).unwrap_or("treble");
    let canon = crate::lilypond::canonical_clef(s);
    allocate_output_bytes(canon.as_bytes(), out_len_ptr)
}

/// Standalone scalar helpers for fast zero-overhead calling
#[no_mangle]
pub extern "C" fn wasm_diatonic_to_midi(d: i32, alter: i32) -> i32 {
    crate::pitch::diatonic_to_midi(d, alter)
}

#[no_mangle]
pub extern "C" fn wasm_key_alter(key: i32, step: i32) -> i32 {
    crate::pitch::key_alter(key, step)
}

// <!-- APAF Bioinformatics | wasm_api.rs | Approved | 2026-10-28 -->
