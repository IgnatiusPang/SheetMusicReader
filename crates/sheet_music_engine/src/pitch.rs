//! Diatonic pitch mapping, key alteration, and LilyPond pitch spelling.

pub const STEP_SEMI: [i32; 7] = [0, 2, 4, 5, 7, 9, 11];
pub const SHARP_ORDER: [i32; 7] = [3, 0, 4, 1, 5, 2, 6];
pub const FLAT_ORDER: [i32; 7] = [6, 2, 5, 1, 4, 0, 3];

/// Calculates MIDI note number from diatonic step (where C4 = 28) and chromatic alteration.
#[inline]
#[must_use]
pub fn diatonic_to_midi(d: i32, alter: i32) -> i32 {
    let oct = d.div_euclid(7);
    let step = d.rem_euclid(7) as usize;
    let semi = match step {
        0 => 0,
        1 => 2,
        2 => 4,
        3 => 5,
        4 => 7,
        5 => 9,
        6 => 11,
        _ => 0,
    };
    12 * (oct + 1) + semi + alter
}

/// Computes the key-signature accidental alteration for a diatonic step in Circle of Fifths.
///
/// Positive keys indicate number of sharps (1..7), negative indicate flats (-1..-7).
#[inline]
#[must_use]
pub fn key_alter(key: i32, step: i32) -> i32 {
    if key > 0 {
        let k = (key as usize).min(7);
        if SHARP_ORDER[..k].contains(&step) {
            1
        } else {
            0
        }
    } else if key < 0 {
        let k = ((-key) as usize).min(7);
        if FLAT_ORDER[..k].contains(&step) {
            -1
        } else {
            0
        }
    } else {
        0
    }
}

/// Writes standard LilyPond pitch representation directly into a formatter or buffer.
pub fn write_lily_pitch<W: std::fmt::Write>(w: &mut W, d: i32, midi: i32) -> std::fmt::Result {
    let base_midi = diatonic_to_midi(d, 0);
    let diff = midi - base_midi;
    let shift = if diff >= 0 {
        (diff + 6) / 12 * 12
    } else {
        (diff - 6) / 12 * 12
    };
    let alter = midi - shift - base_midi;
    let step = d.rem_euclid(7) as usize;
    let base_name = match step {
        0 => "c",
        1 => "d",
        2 => "e",
        3 => "f",
        4 => "g",
        5 => "a",
        6 => "b",
        _ => "c",
    };
    w.write_str(base_name)?;
    if alter > 0 {
        for _ in 0..alter {
            w.write_str("is")?;
        }
    } else if alter < 0 {
        for _ in 0..(-alter) {
            w.write_str("es")?;
        }
    }
    let octv = d.div_euclid(7) + shift / 12;
    if octv > 3 {
        for _ in 0..(octv - 3) {
            w.write_char('\'')?;
        }
    } else if octv < 3 {
        for _ in 0..(3 - octv) {
            w.write_char(',')?;
        }
    }
    Ok(())
}

/// Spells a notehead into standard LilyPond pitch representation (e.g. "c'", "fis''", "bes,").
#[must_use]
pub fn lily_pitch(d: i32, midi: i32) -> String {
    let mut out = String::with_capacity(8);
    let _ = write_lily_pitch(&mut out, d, midi);
    out
}

/// Diatonic index of bottom staff line for standard clefs.
#[must_use]
pub fn clef_bottom(clef: &str) -> i32 {
    match clef {
        "G" => 30,     // Treble: bottom line is E4 (d=30)
        "G8vb" => 23,  // Treble 8vb: E3
        "G8va" => 37,  // Treble 8va: E5
        "F" => 18,     // Bass: bottom line is G2 (d=18)
        "C" => 24,     // Alto: bottom line is F3 (d=24)
        _ => 30,
    }
}

/// Calculates diatonic step index from pixel/point Y coordinate relative to staff lines.
///
/// # Requires: line_spacing > 0.0
#[must_use]
pub fn coordinate_to_diatonic(staff_bottom_y: f32, note_y: f32, line_spacing: f32, clef: &str) -> i32 {
    let step_dist = line_spacing * 0.5;
    let steps_above_bottom = ((staff_bottom_y - note_y) / step_dist.max(1e-4)).round() as i32;
    clef_bottom(clef) + steps_above_bottom
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_diatonic_to_midi_parity() {
        assert_eq!(diatonic_to_midi(28, 0), 60);  // C4
        assert_eq!(diatonic_to_midi(30, 0), 64);  // E4
        assert_eq!(diatonic_to_midi(31, 1), 66);  // F#4
        assert_eq!(diatonic_to_midi(34, -1), 70); // Bb4
        assert_eq!(diatonic_to_midi(18, 0), 43);  // G2
    }

    #[test]
    fn test_key_alterations_circle_of_fifths() {
        // D major (2 sharps: F#, C#)
        assert_eq!(key_alter(2, 3), 1); // F
        assert_eq!(key_alter(2, 0), 1); // C
        assert_eq!(key_alter(2, 4), 0); // G

        // Eb major (3 flats: Bb, Eb, Ab)
        assert_eq!(key_alter(-3, 6), -1); // B
        assert_eq!(key_alter(-3, 2), -1); // E
        assert_eq!(key_alter(-3, 5), -1); // A
        assert_eq!(key_alter(-3, 1), 0);  // D
    }

    #[test]
    fn test_lily_pitch_spelling() {
        assert_eq!(lily_pitch(28, 60), "c'");
        assert_eq!(lily_pitch(30, 64), "e'");
        assert_eq!(lily_pitch(31, 66), "fis'");
        assert_eq!(lily_pitch(34, 70), "bes'");
        assert_eq!(lily_pitch(18, 43), "g,");
    }
}
