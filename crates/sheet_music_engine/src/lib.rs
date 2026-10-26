//! High-performance verified sheet music OMR and engraving engine in Rust.

pub mod lilypond;
pub mod midi;
pub mod omr;
pub mod pitch;
pub mod rhythm;
pub mod wasm_api;

pub use lilypond::{generate_score_document, Measure};
pub use midi::generate_midi;
pub use omr::{detect_staff_systems_from_densities, StaffSystem};
pub use pitch::{diatonic_to_midi, key_alter, lily_pitch};
pub use rhythm::{lily_duration, repair_measure, NoteEvent};
pub use wasm_api::*;
