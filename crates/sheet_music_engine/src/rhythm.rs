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
    #[serde(default)]
    pub beam: Option<String>,
    #[serde(default)]
    pub clef: Option<String>,
    #[serde(default)]
    pub pitch_str: Option<String>,
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
            beam: None,
            clef: None,
            pitch_str: None,
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
            beam: None,
            clef: None,
            pitch_str: None,
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

/// Decomposes a duration deficit into standard LilyPond rest duration values.
#[must_use]
pub fn decompose_deficit(deficit: f64) -> Vec<f64> {
    let mut rem = deficit;
    let mut vals = Vec::new();
    for (val, _) in STANDARD_DURATIONS {
        while rem >= val - 1e-4 {
            vals.push(val);
            rem -= val;
            if rem < 0.01 {
                break;
            }
        }
        if rem < 0.01 {
            break;
        }
    }
    vals
}

/// Workspace Rule 3.7: Restores silent rests in measures with duration deficits.
#[must_use]
pub fn restore_silent_rests(events: &[NoteEvent], expected: f64) -> Vec<NoteEvent> {
    let total: f64 = events.iter().map(|e| e.value).sum();
    if total >= expected - EPS {
        return events.to_vec();
    }
    let deficit = expected - total;
    let rest_vals = decompose_deficit(deficit);
    let mut out = events.to_vec();
    let mut last_x = out.last().map(|e| e.x).unwrap_or(0.0);
    for v in rest_vals {
        last_x += 10.0;
        out.push(NoteEvent::new_rest(last_x, v));
    }
    out
}

/// Workspace Rule 3.8: Automatically beams runs of consecutive short notes (<= 0.5b).
#[must_use]
pub fn apply_stem_beaming(events: &[NoteEvent]) -> Vec<NoteEvent> {
    let mut out = events.to_vec();
    let n = out.len();
    if n < 2 {
        return out;
    }

    let is_beamable = |e: &NoteEvent| -> bool {
        !e.is_rest && !e.midis.is_empty() && e.value <= 0.5 + 1e-4
    };

    let mut start: Option<usize> = None;
    for i in 0..n {
        if is_beamable(&out[i]) {
            if start.is_none() {
                start = Some(i);
            }
        } else if let Some(s) = start {
            if s + 2 <= i && s < out.len() && i <= out.len() {
                if let Some(first) = out.get_mut(s) {
                    first.beam = Some("[".to_string());
                }
                if let Some(last) = out.get_mut(i.saturating_sub(1)) {
                    last.beam = Some("]".to_string());
                }
            }
            start = None;
        }
    }
    if let Some(s) = start {
        if s + 2 <= n && s < out.len() && n <= out.len() {
            if let Some(first) = out.get_mut(s) {
                first.beam = Some("[".to_string());
            }
            if let Some(last) = out.get_mut(n.saturating_sub(1)) {
                last.beam = Some("]".to_string());
            }
        }
    }

    out
}

/// Repairs an overfull or underfull measure.
/// Underfull measures are padded with silent rests (Rule 3.7).
/// Overfull measures are resolved via whole-rest fill, upper stem precedence, or triplets.
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
    if total < expected - EPS {
        return restore_silent_rests(events, expected);
    }
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

    #[test]
    fn test_decompose_deficit() {
        assert_eq!(decompose_deficit(1.0), vec![1.0]);
        assert_eq!(decompose_deficit(1.5), vec![1.5]);
        assert_eq!(decompose_deficit(2.5), vec![2.0, 0.5]);
        assert_eq!(decompose_deficit(0.75), vec![0.75]);
    }

    #[test]
    fn test_restore_silent_rests() {
        // Measure with only 2 beats in 4/4 meter -> restores 2-beat rest
        let events = vec![NoteEvent::new_note(0.0, 2.0, 1, 60)];
        let restored = restore_silent_rests(&events, 4.0);
        assert_eq!(restored.len(), 2);
        assert!(restored[1].is_rest);
        assert!((restored[1].value - 2.0).abs() < 1e-4);

        // repair_measure handles underfull measures
        let repaired = repair_measure(&events, 4.0);
        let sum: f64 = repaired.iter().map(|e| e.value).sum();
        assert!((sum - 4.0).abs() < 1e-4);
    }

    #[test]
    fn test_apply_stem_beaming() {
        let events = vec![
            NoteEvent::new_note(0.0, 0.5, 1, 60), // eighth note
            NoteEvent::new_note(10.0, 0.5, 1, 62), // eighth note
            NoteEvent::new_note(20.0, 1.0, 1, 64), // quarter note
        ];
        let beamed = apply_stem_beaming(&events);
        assert_eq!(beamed[0].beam, Some("[".to_string()));
        assert_eq!(beamed[1].beam, Some("]".to_string()));
        assert_eq!(beamed[2].beam, None);
    }
}

// <!-- APAF Bioinformatics | rhythm.rs | Approved | 2026-10-28 -->
