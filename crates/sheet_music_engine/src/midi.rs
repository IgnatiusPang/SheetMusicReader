//! Verified MIDI standard serialization for sheet_music_engine.
//! Encodes Type 0 Standard MIDI Files (SMF) directly to binary.

use crate::rhythm::NoteEvent;

/// Ticks per quarter note (standard resolution).
pub const TICKS_PER_BEAT: u32 = 480;

/// Writes a Variable-Length Quantity (VLQ) to a byte buffer according to MIDI spec.
/// Unrolled branch logic eliminates indexing hazards and guarantees termination.
pub fn write_vlq(buffer: &mut Vec<u8>, value: u32) {
    if value < 0x80 {
        buffer.push((value & 0x7F) as u8);
    } else if value < 0x4000 {
        buffer.push((((value >> 7) & 0x7F) | 0x80) as u8);
        buffer.push((value & 0x7F) as u8);
    } else if value < 0x200000 {
        buffer.push((((value >> 14) & 0x7F) | 0x80) as u8);
        buffer.push((((value >> 7) & 0x7F) | 0x80) as u8);
        buffer.push((value & 0x7F) as u8);
    } else {
        buffer.push((((value >> 21) & 0x7F) | 0x80) as u8);
        buffer.push((((value >> 14) & 0x7F) | 0x80) as u8);
        buffer.push((((value >> 7) & 0x7F) | 0x80) as u8);
        buffer.push((value & 0x7F) as u8);
    }
}

/// Converts beat duration (1.0 = quarter note) to MIDI ticks.
#[must_use]
pub fn beats_to_ticks(beats: f64) -> u32 {
    let raw = (beats.max(0.0) * TICKS_PER_BEAT as f64).round();
    if raw >= (u32::MAX as f64) {
        u32::MAX
    } else {
        raw as u32
    }
}

/// Generates a complete Type 0 Standard MIDI (.mid) binary file from a slice of NoteEvents.
///
/// # Arguments
/// * `events` - Ordered slice of NoteEvents to encode.
/// * `bpm` - Beats per minute (tempo, default 80 for Dancla Cantabile).
/// * `program` - General MIDI instrument program (e.g. 40 for Violin, 0 for Piano).
#[must_use]
pub fn generate_midi(events: &[NoteEvent], bpm: u32, program: u8) -> Vec<u8> {
    let mut track_data = Vec::with_capacity(events.len() * 8 + 32);

    // 1. Time Signature meta event (4/4 default, delta time 0)
    track_data.push(0x00); // delta time
    track_data.extend_from_slice(&[0xFF, 0x58, 0x04, 0x04, 0x02, 0x18, 0x08]);

    // 2. Tempo meta event: microseconds per beat = 60_000_000 / bpm
    let safe_bpm = bpm.clamp(20, 300);
    let us_per_beat = 60_000_000 / safe_bpm.max(1);
    track_data.push(0x00); // delta time
    track_data.extend_from_slice(&[
        0xFF,
        0x51,
        0x03,
        ((us_per_beat >> 16) & 0xFF) as u8,
        ((us_per_beat >> 8) & 0xFF) as u8,
        (us_per_beat & 0xFF) as u8,
    ]);

    // 3. Program Change (Instrument)
    track_data.push(0x00); // delta time
    track_data.extend_from_slice(&[0xC0, program.min(127)]);

    // 4. Note Events
    let mut pending_rest_ticks: u32 = 0;
    for ev in events {
        let dur_ticks = beats_to_ticks(ev.value);
        if ev.is_rest || ev.midis.is_empty() {
            pending_rest_ticks = pending_rest_ticks.saturating_add(dur_ticks);
        } else {
            let vel: u8 = 88;
            for (idx, &m) in ev.midis.iter().enumerate() {
                let pitch = (m.clamp(0, 127)) as u8;
                let delta = if idx == 0 { pending_rest_ticks } else { 0 };
                write_vlq(&mut track_data, delta);
                track_data.extend_from_slice(&[0x90, pitch, vel]);
            }
            for (idx, &m) in ev.midis.iter().enumerate() {
                let pitch = (m.clamp(0, 127)) as u8;
                let delta = if idx == 0 { dur_ticks.max(1) } else { 0 };
                write_vlq(&mut track_data, delta);
                track_data.extend_from_slice(&[0x80, pitch, 0x00]);
            }
            pending_rest_ticks = 0;
        }
    }

    // 5. End of Track meta event
    write_vlq(&mut track_data, pending_rest_ticks);
    track_data.extend_from_slice(&[0xFF, 0x2F, 0x00]);

    // Assemble Type 0 MIDI File
    let mut file = Vec::with_capacity(14 + 8 + track_data.len());

    // Header Chunk: MThd, length 6, format 0, 1 track, 480 division
    file.extend_from_slice(b"MThd");
    file.extend_from_slice(&6u32.to_be_bytes());
    file.extend_from_slice(&0u16.to_be_bytes()); // format 0
    file.extend_from_slice(&1u16.to_be_bytes()); // 1 track
    file.extend_from_slice(&(TICKS_PER_BEAT as u16).to_be_bytes());

    // Track Chunk: MTrk, length, track_data
    file.extend_from_slice(b"MTrk");
    file.extend_from_slice(&(track_data.len() as u32).to_be_bytes());
    file.extend_from_slice(&track_data);

    file
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vlq_encoding() {
        let mut buf = Vec::new();
        write_vlq(&mut buf, 0);
        assert_eq!(buf, vec![0x00]);

        buf.clear();
        write_vlq(&mut buf, 127);
        assert_eq!(buf, vec![0x7F]);

        buf.clear();
        write_vlq(&mut buf, 128);
        assert_eq!(buf, vec![0x81, 0x00]);

        buf.clear();
        write_vlq(&mut buf, 480);
        assert_eq!(buf, vec![0x83, 0x60]);
    }

    #[test]
    fn test_midi_header_and_track() {
        let events = vec![
            NoteEvent::new_note(0.0, 1.0, 1, 60), // C4 quarter
            NoteEvent::new_note(10.0, 1.0, 1, 64), // E4 quarter
        ];
        let bytes = generate_midi(&events, 80, 40);

        // Check MThd header
        assert_eq!(&bytes[0..4], b"MThd");
        assert_eq!(&bytes[4..8], &[0, 0, 0, 6]);
        assert_eq!(&bytes[8..10], &[0, 0]); // format 0
        assert_eq!(&bytes[10..12], &[0, 1]); // 1 track
        assert_eq!(&bytes[12..14], &[0x01, 0xE0]); // 480 division

        // Check MTrk header
        assert_eq!(&bytes[14..18], b"MTrk");
        let track_len = u32::from_be_bytes([bytes[18], bytes[19], bytes[20], bytes[21]]) as usize;
        assert_eq!(bytes.len(), 22 + track_len);
    }
}
