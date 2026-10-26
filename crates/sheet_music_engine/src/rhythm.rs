//! Rhythm, durations, tuplet scaling, and measure rhythm repair.

use serde::{Deserialize, Serialize};

pub const EPS: f64 = 0.02;

pub const STANDARD_DURATIONS: [(f64, &str); 11] = [
    (4.0, "1"),
    (3.0, "2."),
    (2.0, "2"),
    (1.5, "4."),
    (1.0, "4"),
    (0.75, "8."),
    (0.5, "8"),
    (0.375, "16."),
    (0.25, "16"),
    (0.125, "32"),
    (0.0625, "64"),
];

/// A musical event (note, chord, or rest).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NoteEvent {
    pub x: f32,
    pub value: f64,
    pub is_rest: bool,
    pub stem: i32,
    pub tie: bool,
    pub midis: Vec<i32>,
}

impl NoteEvent {
    #[must_use]
    pub fn new_note(x: f32, value: f64, stem: i32, midi: i32) -> Self {
        Self {
            x,
            value,
            is_rest: false,
            stem,
            tie: false,
            midis: vec![midi],
        }
    }

    #[must_use]
    pub fn new_rest(x: f32, value: f64) -> Self {
        Self {
            x,
            value,
            is_rest: true,
            stem: 0,
            tie: false,
            midis: Vec::new(),
        }
    }
}

/// Computes the best rational fraction approximation of a floating point duration.
#[must_use]
pub fn rational_fraction(val: f64, max_denom: i64) -> (i64, i64) {
    if val <= 0.0 {
        return (0, 1);
    }
    let mut best_n = 1;
    let mut best_d = 1;
    let mut min_err = (val - 1.0).abs();

    for d in 1..=max_denom {
        let n = (val * d as f64).round() as i64;
        let err = (val - (n as f64 / d as f64)).abs();
        if err < min_err {
            min_err = err;
            best_n = n;
            best_d = d;
            if err < 1e-6 {
                break;
            }
        }
    }
    (best_n, best_d)
}

/// Converts a beat duration (in quarter-note = 1.0 or whole-note units) to standard LilyPond duration string.
#[must_use]
pub fn lily_duration(v: f64) -> String {
    for (dur, name) in STANDARD_DURATIONS {
        if (v - dur).abs() < 1e-4 {
            return (*name).to_string();
        }
    }
    let (n, d) = rational_fraction(v, 48);
    format!("4*{}/{}", n, d)
}

/// Repairs an overfull measure by checking whole rests, polyphonic split voices, and triplets.
#[must_use]
pub fn repair_measure(events: &[NoteEvent], expected: f64) -> Vec<NoteEvent> {
    if events.is_empty() {
        return Vec::new();
    }
    // Single whole-rest fills the bar
    if let [first] = events {
        if first.is_rest && (first.value - 4.0).abs() < 1e-4 {
            let mut r = first.clone();
            r.value = expected;
            return vec![r];
        }
    }

    let total: f64 = events.iter().map(|e| e.value).sum();
    if total <= expected + EPS {
        return events.to_vec();
    }

    // Split voice resolution: upper stems take precedence
    let has_up = events.iter().any(|e| !e.is_rest && e.stem > 0);
    let has_dn = events.iter().any(|e| !e.is_rest && e.stem < 0);
    if has_up && has_dn {
        let upper: Vec<NoteEvent> = events
            .iter()
            .filter(|e| e.is_rest || e.stem >= 0)
            .cloned()
            .collect();
        let upper_total: f64 = upper.iter().map(|e| e.value).sum();
        if upper_total <= expected + EPS {
            return upper;
        }
    }

    repair_triplets(events, expected)
}

/// Identifies 3 consecutive equal notes and scales them to triplets to resolve excess rhythm.
#[must_use]
pub fn repair_triplets(events: &[NoteEvent], expected: f64) -> Vec<NoteEvent> {
    let mut out = events.to_vec();
    let total: f64 = out.iter().map(|e| e.value).sum();
    let excess = total - expected;
    if excess <= EPS || out.len() < 3 {
        return out;
    }

    // Find 3 consecutive equal-duration notes whose single value <= excess + EPS
    let mut cand_idx = None;
    for i in 0..=(out.len() - 3) {
        let v0 = out[i].value;
        let v1 = out[i + 1].value;
        let v2 = out[i + 2].value;
        if (v0 - v1).abs() < 1e-4 && (v1 - v2).abs() < 1e-4 && v0 <= excess + EPS {
            cand_idx = Some(i);
            break;
        }
    }

    if let Some(i) = cand_idx {
        if let Some(slice) = out.get_mut(i..=i + 2) {
            for item in slice {
                item.value *= 2.0 / 3.0;
            }
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lily_durations_parity() {
        assert_eq!(lily_duration(1.5), "4.");
        assert_eq!(lily_duration(0.25), "16");
        assert_eq!(lily_duration(3.0), "2.");
        assert_eq!(lily_duration(2.0 / 3.0), "4*2/3");
        assert_eq!(lily_duration(1.0), "4");
        assert_eq!(lily_duration(0.5), "8");
    }

    #[test]
    fn test_whole_rest_fills_bar() {
        let bar = vec![NoteEvent::new_rest(0.0, 4.0)];
        let fixed = repair_measure(&bar, 3.0);
        assert_eq!(fixed.len(), 1);
        assert!((fixed[0].value - 3.0).abs() < 1e-5);
    }

    #[test]
    fn test_triplet_repair() {
        let bar = vec![
            NoteEvent::new_note(0.0, 1.0, 1, 60),
            NoteEvent::new_note(10.0, 1.0, 1, 60),
            NoteEvent::new_note(20.0, 1.0, 1, 60),
            NoteEvent::new_note(30.0, 1.0, 1, 60),
            NoteEvent::new_note(40.0, 1.0, 1, 60),
        ]; // Total = 5.0, expected = 4.0
        let fixed = repair_measure(&bar, 4.0);
        let sum: f64 = fixed.iter().map(|e| e.value).sum();
        assert!((sum - 4.0).abs() < 1e-4);
    }
}
