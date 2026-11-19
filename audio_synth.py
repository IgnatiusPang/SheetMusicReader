"""Audio synthesis and sing-along practice track generator.

Generates clean PCM WAV (and optional MP3 via ffmpeg) with:
- Sustained Vocal Guide tone (harmonics + subtle delayed vibrato) for singing along
- Soft piano / violin synthesis voices
- Optional 1-bar count-in and bar-accented metronome beat clicks
- Soft chord accompaniment backing
"""

from __future__ import annotations

import io
import math
import shutil
import subprocess
import wave
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class AudioEvent:
    """Timed musical note or chord event measured in quarter-note beats."""

    onset_beats: float
    duration_beats: float
    pitches: tuple[int, ...]
    velocity: float = 0.85


def midi_to_freq(midi_pitch: int) -> float:
    """Convert a MIDI note number (69 = A4 = 440 Hz) to frequency in Hz."""
    return 440.0 * (2.0 ** ((float(midi_pitch) - 69.0) / 12.0))


def synthesize_note_wave(
    midi_pitch: int,
    duration_sec: float,
    sr: int = 22050,
    voice: str = "vocal_guide",
    gain: float = 0.38,
) -> np.ndarray:
    """Synthesize a mono float64 waveform for one pitched note."""
    n_samples = max(1, int(round(max(0.02, float(duration_sec)) * sr)))
    t = np.arange(n_samples, dtype=np.float64) / float(sr)
    freq = midi_to_freq(midi_pitch)
    total_dur = float(n_samples) / float(sr)

    voice_norm = (voice or "vocal_guide").lower()
    if voice_norm in ("vocal", "vocal_guide", "voice", "sing"):
        # Smooth sustained harmonic contour with gentle vibrato on held notes
        vib_delay = 0.18
        vib_depth = 0.0025 * np.clip((t - vib_delay) / 0.12, 0.0, 1.0)
        phase = 2.0 * math.pi * freq * t + (
            (vib_depth * freq / 5.2) * (1.0 - np.cos(2.0 * math.pi * 5.2 * np.maximum(0.0, t - vib_delay)))
            if total_dur > 0.32
            else 0.0
        )
        wave_raw = (
            1.00 * np.sin(phase)
            + 0.42 * np.sin(2.0 * phase)
            + 0.18 * np.sin(3.0 * phase)
            + 0.06 * np.sin(4.0 * phase)
        )
        attack = min(0.030, total_dur * 0.20)
        release = min(0.045, total_dur * 0.25)
        att_env = np.clip(t / max(1e-4, attack), 0.0, 1.0)
        rel_env = np.clip((total_dur - t) / max(1e-4, release), 0.0, 1.0)
        env = 0.5 * (1.0 - np.cos(math.pi * att_env)) * np.sin(0.5 * math.pi * rel_env)
    elif voice_norm == "violin":
        phase = 2.0 * math.pi * freq * t
        wave_raw = (
            1.00 * np.sin(phase)
            + 0.55 * np.sin(2.0 * phase)
            + 0.35 * np.sin(3.0 * phase)
            + 0.22 * np.sin(4.0 * phase)
            + 0.10 * np.sin(5.0 * phase)
        )
        attack = min(0.065, total_dur * 0.28)
        release = min(0.050, total_dur * 0.25)
        att_env = np.clip(t / max(1e-4, attack), 0.0, 1.0)
        rel_env = np.clip((total_dur - t) / max(1e-4, release), 0.0, 1.0)
        env = att_env * rel_env
    else:
        # Piano / plucked percussive envelope with natural decay
        phase = 2.0 * math.pi * freq * t
        wave_raw = (
            1.00 * np.sin(phase)
            + 0.48 * np.sin(2.0 * phase) * np.exp(-2.2 * t)
            + 0.22 * np.sin(3.0 * phase) * np.exp(-3.4 * t)
            + 0.10 * np.sin(4.0 * phase) * np.exp(-5.0 * t)
        )
        attack = min(0.012, total_dur * 0.12)
        release = min(0.060, total_dur * 0.30)
        att_env = np.clip(t / max(1e-4, attack), 0.0, 1.0)
        decay_env = np.exp(-1.9 * t)
        rel_env = np.clip((total_dur - t) / max(1e-4, release), 0.0, 1.0)
        env = att_env * (0.28 + 0.72 * decay_env) * rel_env

    peak = float(np.max(np.abs(wave_raw))) if wave_raw.size > 0 else 1.0
    norm_factor = 1.0 / max(1.0, peak)
    return wave_raw * env * (float(gain) * norm_factor)


def synthesize_click_wave(accent: bool = False, sr: int = 22050, gain: float = 0.26) -> np.ndarray:
    """Synthesize a short clean metronome woodblock click."""
    dur = 0.048
    n_samples = max(1, int(round(dur * sr)))
    t = np.arange(n_samples, dtype=np.float64) / float(sr)
    freq = 1280.0 if accent else 880.0
    env = np.exp(-t / 0.011) * np.clip(t / 0.002, 0.0, 1.0)
    return np.sin(2.0 * math.pi * freq * t) * env * float(gain if accent else gain * 0.72)


def _mix_wave_at(buf: np.ndarray, start_idx: int, wave_arr: np.ndarray) -> None:
    if start_idx >= buf.shape[0] or wave_arr.size == 0:
        return
    if start_idx < 0:
        clip_front = -start_idx
        if clip_front >= wave_arr.shape[0]:
            return
        wave_arr = wave_arr[clip_front:]
        start_idx = 0
    avail = min(wave_arr.shape[0], buf.shape[0] - start_idx)
    if avail > 0:
        buf[start_idx : start_idx + avail] += wave_arr[:avail]


def _render_single_audio_event(
    buf: np.ndarray,
    ev: AudioEvent,
    shift_beats: float,
    sec_per_beat: float,
    sr: int,
    voice: str,
    base_gain: float,
) -> None:
    if not ev.pitches or ev.duration_beats <= 0.0:
        return
    start_sec = (ev.onset_beats + shift_beats) * sec_per_beat
    dur_sec = max(0.03, ev.duration_beats * sec_per_beat)
    start_idx = int(round(start_sec * sr))
    n_pitches = max(1, len(ev.pitches))
    per_pitch_gain = base_gain * float(ev.velocity) / math.sqrt(float(n_pitches))
    deque(
        map(
            lambda p: _mix_wave_at(
                buf,
                start_idx,
                synthesize_note_wave(int(p), dur_sec, sr=sr, voice=voice, gain=per_pitch_gain),
            ),
            ev.pitches,
        ),
        maxlen=0,
    )


def _parse_time_sig(time_signature: str) -> tuple[int, int]:
    parts = str(time_signature or "4/4").strip().split("/")
    try:
        num = max(1, int(parts[0]))
        den = max(1, int(parts[1])) if len(parts) > 1 else 4
        return num, den
    except (ValueError, IndexError):
        return 4, 4


def _render_click_at(
    buf: np.ndarray,
    click_idx: int,
    step_sec: float,
    beats_per_bar: int,
    sr: int,
) -> None:
    start_idx = int(round(click_idx * step_sec * sr))
    accent = (click_idx % beats_per_bar) == 0
    _mix_wave_at(buf, start_idx, synthesize_click_wave(accent=accent, sr=sr))


def render_score_float_buffer(
    melody_events: Sequence[AudioEvent],
    time_signature: str = "4/4",
    tempo_bpm: float = 90.0,
    voice: str = "vocal_guide",
    accompaniment_events: Sequence[AudioEvent] = (),
    include_clicks: bool = True,
    count_in_bars: int = 1,
    sr: int = 22050,
) -> np.ndarray:
    """Render melody, optional chords, and optional count-in/beat clicks to float64 samples."""
    bpm = max(10.0, float(tempo_bpm or 90.0))
    sec_per_beat = 60.0 / bpm
    ts_num, ts_den = _parse_time_sig(time_signature)
    click_step_q = 4.0 / float(ts_den)
    bar_beats_q = float(ts_num) * click_step_q
    shift_beats = max(0, int(count_in_bars)) * bar_beats_q

    all_events: Iterable[AudioEvent] = (*melody_events, *accompaniment_events)
    max_music_beats = max(
        map(lambda ev: float(ev.onset_beats) + float(ev.duration_beats), all_events),
        default=0.0,
    )
    total_beats = shift_beats + max_music_beats
    total_sec = total_beats * sec_per_beat + 0.35
    n_samples = max(sr // 4, int(math.ceil(total_sec * sr)))
    buf = np.zeros(n_samples, dtype=np.float64)

    deque(
        map(
            lambda ev: _render_single_audio_event(
                buf, ev, shift_beats, sec_per_beat, sr, voice=voice, base_gain=0.45
            ),
            melody_events,
        ),
        maxlen=0,
    )

    deque(
        map(
            lambda ev: _render_single_audio_event(
                buf, ev, shift_beats, sec_per_beat, sr, voice="piano", base_gain=0.18
            ),
            accompaniment_events,
        ),
        maxlen=0,
    )

    if include_clicks and total_beats > 0.0:
        n_clicks = max(1, int(math.floor((total_beats - 1e-6) / click_step_q)) + 1)
        step_sec = click_step_q * sec_per_beat
        deque(
            map(lambda i: _render_click_at(buf, i, step_sec, ts_num, sr), range(n_clicks)),
            maxlen=0,
        )

    peak = float(np.max(np.abs(buf))) if buf.size > 0 else 0.0
    if peak > 0.90:
        buf *= 0.88 / peak
    return np.clip(buf, -0.98, 0.98)


def render_wav_bytes(
    melody_events: Sequence[AudioEvent],
    time_signature: str = "4/4",
    tempo_bpm: float = 90.0,
    voice: str = "vocal_guide",
    accompaniment_events: Sequence[AudioEvent] = (),
    include_clicks: bool = True,
    count_in_bars: int = 1,
    sr: int = 22050,
) -> bytes:
    """Render audio events directly into 16-bit PCM WAV bytes."""
    buf = render_score_float_buffer(
        melody_events=melody_events,
        time_signature=time_signature,
        tempo_bpm=tempo_bpm,
        voice=voice,
        accompaniment_events=accompaniment_events,
        include_clicks=include_clicks,
        count_in_bars=count_in_bars,
        sr=sr,
    )
    pcm = (buf * 32767.0).astype("<i2")
    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out.getvalue()


def write_wav_file(
    out_path: Path,
    melody_events: Sequence[AudioEvent],
    time_signature: str = "4/4",
    tempo_bpm: float = 90.0,
    voice: str = "vocal_guide",
    accompaniment_events: Sequence[AudioEvent] = (),
    include_clicks: bool = True,
    count_in_bars: int = 1,
    sr: int = 22050,
) -> Path:
    """Write a 16-bit PCM WAV practice track to disk."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wav_bytes = render_wav_bytes(
        melody_events=melody_events,
        time_signature=time_signature,
        tempo_bpm=tempo_bpm,
        voice=voice,
        accompaniment_events=accompaniment_events,
        include_clicks=include_clicks,
        count_in_bars=count_in_bars,
        sr=sr,
    )
    out_path.write_bytes(wav_bytes)
    return out_path


def convert_wav_to_mp3(wav_path: Path, mp3_path: Path | None = None) -> Path:
    """Encode an existing WAV file to MP3 using ffmpeg."""
    wav_path = Path(wav_path)
    target = Path(mp3_path) if mp3_path is not None else wav_path.with_suffix(".mp3")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg executable is not available on PATH")
    target.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [ffmpeg, "-y", "-i", str(wav_path), "-vn", "-ar", "22050", "-b:a", "160k", str(target)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({proc.returncode}): {proc.stderr.strip()}")
    return target


def play_wav(wav_path: Path) -> None:
    """Play a WAV file synchronously via macOS afplay if available."""
    afplay = shutil.which("afplay")
    if not afplay:
        raise FileNotFoundError("afplay is not available on this system")
    subprocess.run([afplay, str(wav_path)], check=True)


# <!-- APAF Bioinformatics | audio_synth.py | Approved | 2026-11-15 -->
