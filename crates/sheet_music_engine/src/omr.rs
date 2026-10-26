//! Optical Music Recognition (OMR) grid analysis and staff system detection.

use crate::pitch::{clef_bottom, key_alter};
use crate::rhythm::NoteEvent;
use serde::{Deserialize, Serialize};

/// Represents a detected 5-line staff system on a musical score.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StaffSystem {
    pub top_y: f32,
    pub bottom_y: f32,
    pub line_spacing: f32,
    pub left_x: f32,
    pub right_x: f32,
    pub lines: [f32; 5],
}

impl StaffSystem {
    #[must_use]
    pub fn new(lines: [f32; 5], left_x: f32, right_x: f32) -> Self {
        let [top_y, _, _, _, bottom_y] = lines;
        let line_spacing = ((bottom_y - top_y).abs() * 0.25).max(1.0);
        Self {
            top_y,
            bottom_y,
            line_spacing,
            left_x,
            right_x,
            lines,
        }
    }

    /// Converts a notehead Y coordinate into a diatonic step number.
    #[must_use]
    pub fn coordinate_to_diatonic(&self, note_y: f32, clef: &str) -> i32 {
        let step_dist = self.line_spacing * 0.5;
        let steps_above_bottom = ((self.bottom_y - note_y) / step_dist.max(1e-4)).round() as i32;
        clef_bottom(clef) + steps_above_bottom
    }

    /// Converts a notehead to a complete NoteEvent with pitch and MIDI.
    #[must_use]
    pub fn notehead_to_event(
        &self,
        x: f32,
        y: f32,
        is_hollow: bool,
        stem_up: bool,
        clef: &str,
        key: i32,
    ) -> NoteEvent {
        let diatonic = self.coordinate_to_diatonic(y, clef);
        let step = diatonic.rem_euclid(7);
        let alter = key_alter(key, step);
        let midi = crate::pitch::diatonic_to_midi(diatonic, alter);
        let val = if is_hollow { 2.0 } else { 1.0 };
        let stem = if stem_up { 1 } else { -1 };
        NoteEvent::new_note(x, val, stem, midi)
    }
}

/// Detects horizontal staff lines from a grayscale image projection buffer.
/// `row_densities` contains the fraction of dark pixels for each vertical row.
#[must_use]
pub fn detect_staff_systems_from_densities(
    row_densities: &[f32],
    min_density: f32,
    width: f32,
) -> Vec<StaffSystem> {
    if row_densities.len() < 5 {
        return Vec::new();
    }

    // 1. Find local peaks above min_density threshold
    let mut peaks = Vec::new();
    for i in 1..(row_densities.len().saturating_sub(1)) {
        let prev = row_densities.get(i.saturating_sub(1)).copied().unwrap_or(0.0);
        let curr = row_densities.get(i).copied().unwrap_or(0.0);
        let next = row_densities.get(i.saturating_add(1)).copied().unwrap_or(0.0);

        if curr >= min_density && curr >= prev && curr >= next {
            peaks.push(i as f32);
        }
    }

    // 2. Group peaks into 5-line staff systems with uniform spacing via windows
    let mut systems = Vec::new();
    let mut last_bottom = -100.0f32;
    for w in peaks.windows(5) {
        if let [l0, l1, l2, l3, l4] = *w {
            if l0 <= last_bottom {
                continue;
            }
            let s1 = l1 - l0;
            let s2 = l2 - l1;
            let s3 = l3 - l2;
            let s4 = l4 - l3;
            let avg_s = (s1 + s2 + s3 + s4) * 0.25;

            // Check uniformity of staff spacing within 25% tolerance
            if (s1 - avg_s).abs() < avg_s * 0.25
                && (s2 - avg_s).abs() < avg_s * 0.25
                && (s3 - avg_s).abs() < avg_s * 0.25
                && (s4 - avg_s).abs() < avg_s * 0.25
                && avg_s >= 4.0
            {
                systems.push(StaffSystem::new([l0, l1, l2, l3, l4], 0.0, width));
                last_bottom = l4;
            }
        }
    }

    systems
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_staff_system_diatonic_mapping() {
        // Line spacing 12.0px, lines at y = [28, 40, 52, 64, 76]
        // Bottom line E4 is at y = 76.0 (step 0 = E4, diatonic 30)
        let sys = StaffSystem::new([28.0, 40.0, 52.0, 64.0, 76.0], 0.0, 800.0);
        assert_eq!(sys.coordinate_to_diatonic(76.0, "treble"), 30); // E4
        assert_eq!(sys.coordinate_to_diatonic(70.0, "treble"), 31); // F4 (space 1)
        assert_eq!(sys.coordinate_to_diatonic(64.0, "treble"), 32); // G4 (line 2)
        assert_eq!(sys.coordinate_to_diatonic(28.0, "treble"), 38); // F5 (line 5)
    }

    #[test]
    fn test_detect_staff_systems_uniform() {
        let mut densities = vec![0.0f32; 100];
        // Create 5 peaks at y = 20, 32, 44, 56, 68
        densities[20] = 0.8;
        densities[32] = 0.8;
        densities[44] = 0.8;
        densities[56] = 0.8;
        densities[68] = 0.8;

        let systems = detect_staff_systems_from_densities(&densities, 0.5, 600.0);
        assert_eq!(systems.len(), 1);
        assert_eq!(systems[0].top_y, 20.0);
        assert_eq!(systems[0].bottom_y, 68.0);
        assert_eq!(systems[0].line_spacing, 12.0);
    }
}
