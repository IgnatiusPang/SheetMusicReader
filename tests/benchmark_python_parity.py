"""Differential Parity and Comparative Benchmark: Python (vector_omr) vs Rust (sheet_music_engine)."""
import time
import subprocess
from pathlib import Path
import vector_omr as v

ROOT = Path(__file__).resolve().parents[1]

def run_python_benchmark():
    print("=== Sheet Music Engine Python Benchmark ===")
    n_trials = 100_000

    # 1. Diatonic to MIDI (100,000)
    t0 = time.perf_counter()
    checksum = 0
    for i in range(n_trials):
        d = (i % 80) - 20
        alter = (i % 5) - 2
        checksum += v.diatonic_to_midi(d, alter)
    t_midi = time.perf_counter() - t0
    ns_midi = (t_midi / n_trials) * 1e9
    print(f"Python Diatonic-to-MIDI: {t_midi*1000:.2f} ms ({ns_midi:.2f} ns/call, checksum={checksum})")

    # 2. Key Alteration (100,000)
    t0 = time.perf_counter()
    alter_sum = 0
    for i in range(n_trials):
        key = (i % 15) - 7
        step = i % 7
        alter_sum += v.key_alter(key, step)
    t_key = time.perf_counter() - t0
    ns_key = (t_key / n_trials) * 1e9
    print(f"Python Key-Alteration: {t_key*1000:.2f} ms ({ns_key:.2f} ns/call, checksum={alter_sum})")

    # 3. LilyPond Duration (100,000)
    test_durs = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.375, 0.25, 0.125, 2.0 / 3.0]
    t0 = time.perf_counter()
    total_chars = 0
    for i in range(n_trials):
        val = test_durs[i % len(test_durs)]
        total_chars += len(v.lily_duration(val))
    t_dur = time.perf_counter() - t0
    ns_dur = (t_dur / n_trials) * 1e9
    print(f"Python Lily Duration: {t_dur*1000:.2f} ms ({ns_dur:.2f} ns/call, total_chars={total_chars})")

    # 4. LilyPond Pitch Spelling (100,000)
    t0 = time.perf_counter()
    total_pitch_chars = 0
    for i in range(n_trials):
        d = (i % 40) + 10
        alter = (i % 3) - 1
        m = v.diatonic_to_midi(d, alter)
        head = v.Head(0, 0, 6, 1.0, d, m, 1, 0, 0, 1.0)
        total_pitch_chars += len(v.lily_pitch(head))
    t_pitch = time.perf_counter() - t0
    ns_pitch = (t_pitch / n_trials) * 1e9
    print(f"Python Lily Pitch: {t_pitch*1000:.2f} ms ({ns_pitch:.2f} ns/call, total_chars={total_pitch_chars})")

    # 5. Rhythm Repair (50,000)
    m_trials = 50_000
    base_bar = (
        v.Event(0.0, 1.0, (v.Head(0, 0, 6, 1.0, 28, 60, 1, 0, 0, 1.0),), 1),
        v.Event(10.0, 1.0, (v.Head(10, 0, 6, 1.0, 29, 62, 1, 0, 0, 1.0),), 1),
        v.Event(20.0, 1.0, (v.Head(20, 0, 6, 1.0, 30, 64, 1, 0, 0, 1.0),), 1),
        v.Event(30.0, 1.0, (v.Head(30, 0, 6, 1.0, 31, 65, 1, 0, 0, 1.0),), 1),
        v.Event(40.0, 1.0, (v.Head(40, 0, 6, 1.0, 32, 67, 1, 0, 0, 1.0),), 1),
    )
    t0 = time.perf_counter()
    rep_count = 0
    for _ in range(m_trials):
        fixed = v.repair(base_bar, 4.0)
        rep_count += len(fixed)
    t_repair = time.perf_counter() - t0
    us_repair = (t_repair / m_trials) * 1e6
    print(f"Python Rhythm Repair: {t_repair*1000:.2f} ms ({us_repair:.2f} us/bar, total_events={rep_count})")

    return {
        "midi_ns": ns_midi,
        "key_ns": ns_key,
        "dur_ns": ns_dur,
        "pitch_ns": ns_pitch,
        "repair_us": us_repair,
        "midi_checksum": checksum,
        "key_checksum": alter_sum,
        "dur_chars": total_chars,
        "pitch_chars": total_pitch_chars,
    }

if __name__ == "__main__":
    run_python_benchmark()
