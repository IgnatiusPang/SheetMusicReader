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

/// Canonicalizes LilyPond clef strings into Western notation families.
#[must_use]
pub fn canonical_clef(raw: &str) -> &'static str {
    let clean: String = raw
        .chars()
        .filter(|c| !matches!(c, '"' | '\'' | '(' | ')' | '[' | ']'))
        .collect();
    let lower = clean.trim().to_lowercase();
    if lower.starts_with("treble")
        || lower.starts_with("violin")
        || lower.starts_with("french")
        || matches!(
            lower.as_str(),
            "g" | "g1" | "g2" | "g_8" | "g^8" | "g8" | "treble_8" | "treble^8"
        )
    {
        return "treble";
    }
    if lower.starts_with("bass")
        || lower.starts_with("subbass")
        || matches!(
            lower.as_str(),
            "f" | "f3" | "f4" | "f5" | "f_8" | "f_15" | "f8"
        )
    {
        return "bass";
    }
    if lower.starts_with("alto")
        || lower.starts_with("soprano")
        || lower.starts_with("mezzo")
        || matches!(lower.as_str(), "c" | "c1" | "c2" | "c3")
    {
        return "alto";
    }
    if lower.starts_with("tenor")
        || lower.starts_with("baritone")
        || matches!(lower.as_str(), "c4" | "c5")
    {
        return "tenor";
    }
    if lower.starts_with("perc") {
        return "percussion";
    }
    "treble"
}

/// Returns the LilyPond clef identifier for standard clef tags.
#[must_use]
pub fn clef_name(clef: &str) -> &'static str {
    match clef {
        "G" => "treble",
        "G8vb" | "treble_8" => "\"treble_8\"",
        "G8va" | "treble^8" => "\"treble^8\"",
        "F" => "bass",
        "F8vb" | "bass_8" => "\"bass_8\"",
        "C" => "alto",
        _ => canonical_clef(clef),
    }
}

/// Formats a list of NoteEvents into LilyPond note/rest syntax.
#[must_use]
pub fn format_events(events: &[NoteEvent]) -> String {
    let mut out = String::new();
    for (i, ev) in events.iter().enumerate() {
        if i > 0 {
            out.push(' ');
        }
        if let Some(c) = &ev.clef {
            out.push_str(&format!("\\clef {} ", clef_name(c)));
        }
        let dur = lily_duration(ev.value);
        if ev.is_rest || (ev.midis.is_empty() && ev.pitch_str.is_none()) {
            out.push('r');
            out.push_str(&dur);
        } else if let Some(p) = &ev.pitch_str {
            out.push_str(p);
            out.push_str(&dur);
        } else if ev.midis.len() == 1 {
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
        if let Some(b) = &ev.beam {
            out.push_str(b);
        }
    }
    out
}

/// A parsed measure of music with meter, key, events, and optional polyphonic voices.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Measure {
    pub time: (u32, u32),
    pub key: i32,
    pub clef: String,
    #[serde(default)]
    pub events: Vec<NoteEvent>,
    #[serde(default)]
    pub voices: Option<Vec<Vec<NoteEvent>>>,
    #[serde(default)]
    pub expected: f64,
}

impl Measure {
    #[must_use]
    pub fn new(time: (u32, u32), key: i32, clef: &str, events: Vec<NoteEvent>) -> Self {
        let den = time.1 as f64;
        let expected = if den == 0.0 {
            4.0
        } else {
            time.0 as f64 * (4.0 / den.max(1.0))
        };
        Self {
            time,
            key,
            clef: clef.to_string(),
            events,
            voices: None,
            expected,
        }
    }

    #[must_use]
    pub fn with_voices(
        time: (u32, u32),
        key: i32,
        clef: &str,
        voices: Vec<Vec<NoteEvent>>,
    ) -> Self {
        let den = time.1 as f64;
        let expected = if den == 0.0 {
            4.0
        } else {
            time.0 as f64 * (4.0 / den.max(1.0))
        };
        let events = voices.first().cloned().unwrap_or_default();
        Self {
            time,
            key,
            clef: clef.to_string(),
            events,
            voices: Some(voices),
            expected,
        }
    }

    /// Total beat duration of events in the measure.
    #[must_use]
    pub fn total_duration(&self) -> f64 {
        if let Some(voices) = &self.voices {
            if let Some(v0) = voices.first() {
                return v0.iter().map(|e| e.value).sum();
            }
        }
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

        // Polyphonic voices (<< { v1 } \\ { v2 } >>) or single voice
        if let Some(voices) = &self.voices {
            if voices.len() > 1 {
                let v_strs: Vec<String> = voices.iter().map(|v| format_events(v)).collect();
                out.push_str("<< { ");
                out.push_str(&v_strs.join(" } \\\\ { "));
                out.push_str(" } >> \\bar \"|\"");
                return out;
            }
        }

        let evs = if self.events.is_empty() {
            self.voices
                .as_ref()
                .and_then(|v| v.first())
                .map(|v| v.as_slice())
                .unwrap_or(&[])
        } else {
            &self.events
        };

        out.push_str(&format_events(evs));
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

/// Generates a complete standalone LilyPond document for a multi-staff score.
#[must_use]
pub fn generate_multistaff_score_document(title: &str, staves: &[Vec<Measure>]) -> String {
    if staves.len() <= 1 {
        return generate_score_document(
            title,
            staves.first().map(|v| v.as_slice()).unwrap_or(&[]),
        );
    }

    let mut doc = String::new();
    doc.push_str("\\version \"2.26.0\"\n");
    doc.push_str(&format!(
        "\\header {{\n  title = \"{}\"\n  tagline = ##f\n}}\n",
        title
    ));
    doc.push_str("\\paper {\n  #(set-paper-size \"a4\")\n  indent = 0\n}\n");

    let is_piano = staves.len() == 2;
    if is_piano {
        doc.push_str("\\score {\n  \\new PianoStaff <<\n");
    } else {
        doc.push_str("\\score {\n  \\new StaffGroup <<\n");
    }

    for staff_measures in staves {
        doc.push_str("    \\new Staff {\n      \\accidentalStyle modern\n");
        let mut prev: Option<&Measure> = None;
        for (i, m) in staff_measures.iter().enumerate() {
            doc.push_str("      ");
            doc.push_str(&m.to_lilypond(prev));
            doc.push('\n');
            prev = Some(m);
            if (i + 1) % 4 == 0 && (i + 1) < staff_measures.len() {
                doc.push_str("      \\break\n");
            }
        }
        doc.push_str("      \\bar \"|.\"\n    }\n");
    }

    doc.push_str("  >>\n  \\layout { }\n  \\midi { }\n}\n");
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
        assert_eq!(clef_name("french"), "treble");
        assert_eq!(clef_name("subbass"), "bass");
        assert_eq!(clef_name("soprano"), "alto");
        assert_eq!(clef_name("tenor"), "tenor");
        assert_eq!(clef_name("percussion"), "percussion");
        assert_eq!(clef_name("foo"), "treble"); // Unknown clef fallback
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

    #[test]
    fn test_polyphonic_measure() {
        let v1 = vec![
            NoteEvent::new_note(0.0, 2.0, 1, 67), // g'2
            NoteEvent::new_note(20.0, 2.0, 1, 69), // a'2
        ];
        let v2 = vec![
            NoteEvent::new_note(0.0, 4.0, -1, 60), // c'1
        ];
        let m = Measure::with_voices((4, 4), 0, "treble", vec![v1, v2]);
        let lily = m.to_lilypond(None);
        assert!(lily.contains("<< {"));
        assert!(lily.contains("g'2 a'2"));
        assert!(lily.contains("\\\\"));
        assert!(lily.contains("c'1"));
        assert!(lily.contains("} >>"));
    }
}

// <!-- APAF Bioinformatics | lilypond.rs | Approved | 2026-10-28 -->
