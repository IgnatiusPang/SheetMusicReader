//! LilyPond score serialization and engraving syntax generator.

use crate::pitch::lily_pitch;
use crate::rhythm::{lily_duration, NoteEvent};
use serde::{Deserialize, Serialize};

/// Returns the LilyPond key signature name for a given circle-of-fifths key count.
#[must_use]
pub fn key_name(key: i32) -> &'static str {
    match key {
        0 => "c",
        1 => "g",
        2 => "d",
        3 => "a",
        4 => "e",
        5 => "b",
        6 => "fis",
        7 => "cis",
        -1 => "f",
        -2 => "bes",
        -3 => "es",
        -4 => "as",
        -5 => "des",
        -6 => "ges",
        -7 => "ces",
        _ => "c",
    }
}

/// Returns the LilyPond clef identifier for standard clef tags.
#[must_use]
pub fn clef_name(clef: &str) -> &'static str {
    match clef {
        "G" => "treble",
        "G8vb" => "\"treble_8\"",
        "G8va" => "\"treble^8\"",
        "F" => "bass",
        "C" => "alto",
        _ => "treble",
    }
}

/// A parsed measure of music with meter, key, and events.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Measure {
    pub time: (u32, u32),
    pub key: i32,
    pub clef: String,
    pub events: Vec<NoteEvent>,
    #[serde(default)]
    pub expected: f64,
}

impl Measure {
    #[must_use]
    pub fn new(time: (u32, u32), key: i32, clef: &str, events: Vec<NoteEvent>) -> Self {
        let den = time.1 as f64;
        if den == 0.0 {
            return Self {
                time: (time.0, 4),
                key,
                clef: clef.to_string(),
                events,
                expected: 4.0,
            };
        }
        let expected = time.0 as f64 * (4.0 / den.max(1.0));
        Self {
            time,
            key,
            clef: clef.to_string(),
            events,
            expected,
        }
    }

    /// Total beat duration of events in the measure.
    #[must_use]
    pub fn total_duration(&self) -> f64 {
        self.events.iter().map(|e| e.value).sum()
    }

    /// Serializes the measure to LilyPond syntax.
    #[must_use]
    pub fn to_lilypond(&self, prev: Option<&Measure>) -> String {
        let mut out = String::new();

        // Meter change
        if prev.is_none() || prev.map(|p| p.time) != Some(self.time) {
            out.push_str(&format!("\\time {}/{} ", self.time.0, self.time.1));
        }

        // Key change
        if prev.is_none() || prev.map(|p| p.key) != Some(self.key) {
            out.push_str(&format!("\\key {} \\major ", key_name(self.key)));
        }

        // Clef change
        if prev.is_none() || prev.map(|p| &p.clef) != Some(&self.clef) {
            out.push_str(&format!("\\clef {} ", clef_name(&self.clef)));
        }

        // Notes and rests
        for (i, ev) in self.events.iter().enumerate() {
            if i > 0 {
                out.push(' ');
            }
            let dur = lily_duration(ev.value);
            if ev.is_rest || ev.midis.is_empty() {
                out.push('r');
                out.push_str(&dur);
            } else if ev.midis.len() == 1 {
                // Approximate diatonic step from midi for standalone events
                let d = midi_to_approx_diatonic(ev.midis[0]);
                out.push_str(&lily_pitch(d, ev.midis[0]));
                out.push_str(&dur);
            } else {
                out.push('<');
                let mut sorted = ev.midis.clone();
                sorted.sort_unstable();
                for (j, &m) in sorted.iter().enumerate() {
                    if j > 0 {
                        out.push(' ');
                    }
                    let d = midi_to_approx_diatonic(m);
                    out.push_str(&lily_pitch(d, m));
                }
                out.push('>');
                out.push_str(&dur);
            }
            if ev.tie {
                out.push('~');
            }
        }

        out.push_str(" \\bar \"|\"");
        out
    }
}

/// Helper mapping standard MIDI pitch to diatonic step index for standalone events.
#[must_use]
pub fn midi_to_approx_diatonic(midi: i32) -> i32 {
    let oct = (midi - 12) / 12;
    let semi = (midi - 12) % 12;
    let step = match semi {
        0 => 0,  // C
        1 => 0,  // C#
        2 => 1,  // D
        3 => 1,  // D#
        4 => 2,  // E
        5 => 3,  // F
        6 => 3,  // F#
        7 => 4,  // G
        8 => 4,  // G#
        9 => 5,  // A
        10 => 5, // A#
        11 => 6, // B
        _ => 0,
    };
    oct * 7 + step
}

/// Generates a complete standalone LilyPond document for a score.
#[must_use]
pub fn generate_score_document(title: &str, measures: &[Measure]) -> String {
    let mut doc = String::new();
    doc.push_str("\\version \"2.26.0\"\n");
    doc.push_str(&format!(
        "\\header {{\n  title = \"{}\"\n  tagline = ##f\n}}\n",
        title
    ));
    doc.push_str("\\paper {\n  #(set-paper-size \"a4\")\n  indent = 0\n}\n");
    doc.push_str("\\score {\n  \\new Staff {\n    \\accidentalStyle modern\n");

    let mut prev: Option<&Measure> = None;
    for (i, m) in measures.iter().enumerate() {
        doc.push_str("    ");
        doc.push_str(&m.to_lilypond(prev));
        doc.push('\n');
        prev = Some(m);
        if (i + 1) % 4 == 0 {
            doc.push_str("    \\break\n");
        }
    }

    doc.push_str("    \\bar \"|.\"\n  }\n  \\layout { }\n  \\midi { }\n}\n");
    doc
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_key_names() {
        assert_eq!(key_name(0), "c");
        assert_eq!(key_name(2), "d");
        assert_eq!(key_name(-3), "es");
        assert_eq!(key_name(4), "e");
    }

    #[test]
    fn test_clef_names() {
        assert_eq!(clef_name("G"), "treble");
        assert_eq!(clef_name("F"), "bass");
        assert_eq!(clef_name("C"), "alto");
    }

    #[test]
    fn test_measure_serialization() {
        let events = vec![
            NoteEvent::new_note(0.0, 1.0, 1, 60), // c'4
            NoteEvent::new_note(10.0, 1.0, 1, 62), // d'4
            NoteEvent::new_note(20.0, 1.0, 1, 64), // e'4
            NoteEvent::new_note(30.0, 1.0, 1, 65), // f'4
        ];
        let m = Measure::new((4, 4), 0, "G", events);
        let lily = m.to_lilypond(None);
        assert!(lily.contains("\\time 4/4"));
        assert!(lily.contains("\\key c \\major"));
        assert!(lily.contains("\\clef treble"));
        assert!(lily.contains("c'4 d'4 e'4 f'4"));
    }
}
