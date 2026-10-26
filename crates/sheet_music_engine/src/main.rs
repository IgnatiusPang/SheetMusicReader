//! Standalone benchmark and verification CLI for sheet_music_engine.

use sheet_music_engine::pitch::{diatonic_to_midi, key_alter, lily_pitch};
use sheet_music_engine::rhythm::{lily_duration, repair_measure, NoteEvent};
use std::time::Instant;

fn main() {
    println!("=== Sheet Music Engine Rust Benchmark & Parity Suite ===");

    // 1. Diatonic to MIDI Benchmark (100,000 iterations)
    let n_trials = 100_000;
    let start = Instant::now();
    let mut checksum: i64 = 0;
    for i in 0..n_trials {
        let d = (i % 80) as i32 - 20;
        let alter = (i % 5) as i32 - 2;
        let midi = diatonic_to_midi(d, alter);
        checksum += midi as i64;
    }
    let elapsed = start.elapsed();
    let ns_per_call = elapsed.as_nanos() as f64 / (n_trials as f64).max(1.0);
    println!(
        "Diatonic-to-MIDI ({} calls): {:?} total ({:.2} ns/call, checksum={})",
        n_trials, elapsed, ns_per_call, checksum
    );

    // 2. Key Alteration Circle of Fifths Benchmark (100,000 iterations)
    let start = Instant::now();
    let mut alter_sum: i64 = 0;
    for i in 0..n_trials {
        let key = (i % 15) as i32 - 7;
        let step = (i % 7) as i32;
        let alt = key_alter(key, step);
        alter_sum += alt as i64;
    }
    let elapsed = start.elapsed();
    let ns_per_call = elapsed.as_nanos() as f64 / (n_trials as f64).max(1.0);
    println!(
        "Key-Alteration ({} calls): {:?} total ({:.2} ns/call, checksum={})",
        n_trials, elapsed, ns_per_call, alter_sum
    );

    // 3. LilyPond Duration Serialization (100,000 iterations)
    let test_durs = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.375, 0.25, 0.125, 2.0 / 3.0];
    let start = Instant::now();
    let mut total_chars: usize = 0;
    for &v in test_durs.iter().cycle().take(n_trials) {
        let s = lily_duration(v);
        total_chars += s.len();
    }
    let elapsed = start.elapsed();
    let ns_per_call = elapsed.as_nanos() as f64 / (n_trials as f64).max(1.0);
    println!(
        "LilyPond Duration ({} calls): {:?} total ({:.2} ns/call, total_chars={})",
        n_trials, elapsed, ns_per_call, total_chars
    );

    // 4. LilyPond Pitch Spelling (100,000 iterations)
    let start = Instant::now();
    let mut total_pitch_chars: usize = 0;
    for i in 0..n_trials {
        let d = (i % 40) as i32 + 10;
        let alter = (i % 3) as i32 - 1;
        let midi = diatonic_to_midi(d, alter);
        let s = lily_pitch(d, midi);
        total_pitch_chars += s.len();
    }
    let elapsed = start.elapsed();
    let ns_per_call = elapsed.as_nanos() as f64 / (n_trials as f64).max(1.0);
    println!(
        "LilyPond Pitch Spelling ({} calls): {:?} total ({:.2} ns/call, total_chars={})",
        n_trials, elapsed, ns_per_call, total_pitch_chars
    );

    // 5. Measure Rhythm Repair (50,000 measures)
    let m_trials = 50_000;
    let base_bar = vec![
        NoteEvent::new_note(0.0, 1.0, 1, 60),
        NoteEvent::new_note(10.0, 1.0, 1, 62),
        NoteEvent::new_note(20.0, 1.0, 1, 64),
        NoteEvent::new_note(30.0, 1.0, 1, 65),
        NoteEvent::new_note(40.0, 1.0, 1, 67),
    ];
    let start = Instant::now();
    let mut repaired_count: usize = 0;
    for _ in 0..m_trials {
        let fixed = repair_measure(&base_bar, 4.0);
        repaired_count += fixed.len();
    }
    let elapsed = start.elapsed();
    let us_per_bar = elapsed.as_micros() as f64 / (m_trials as f64).max(1.0);
    println!(
        "Rhythm Repair ({} bars): {:?} total ({:.3} us/bar, total_events={})",
        m_trials, elapsed, us_per_bar, repaired_count
    );

    // 6. Extreme Boundary Fuzzing (1,000,000 trials - verify zero panics)
    let f_trials = 1_000_000;
    let start = Instant::now();
    for i in 0..f_trials {
        let d = i - 500_000;
        let alter = (i % 21) - 10;
        let m = diatonic_to_midi(d, alter);
        let _ = lily_pitch(d, m);
        let _ = key_alter(alter, d.rem_euclid(7));
    }
    let elapsed = start.elapsed();
    println!(
        "Fuzzing Extreme Range [-500k..+500k] ({} trials): {:?} - ZERO PANICS VERIFIED",
        f_trials, elapsed
    );
}
