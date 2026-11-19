/**
 * High-Fidelity Web Audio API Realistic Piano Synthesizer
 * Uses multi-harmonic overtone modeling, hammer attack noise transient,
 * string resonance filter, and exponential ADSR decay to emulate an acoustic grand piano.
 */
class PianoSynthesizer {
    constructor() {
        this.ctx = null;
        this.masterGain = null;
        this.activeNodes = [];
        this.voiceMode = 'vocal_guide';
    }

    init() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContext();
            this.masterGain = this.ctx.createGain();
            this.masterGain.gain.value = 0.8;
            this.masterGain.connect(this.ctx.destination);
        }
        if (this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    // Convert MIDI pitch number to frequency in Hz (A440)
    midiToFreq(midi) {
        return 440 * Math.pow(2, (midi - 69) / 12);
    }

    /**
     * Play realistic acoustic piano note
     * @param {number} midiPitch MIDI note number (e.g. 60 for C4)
     * @param {number} durationSeconds Duration in seconds
     * @param {number} velocity Velocity between 0.0 and 1.0
     * @param {number} startTime Optional AudioContext start time offset
     */
    playNote(midiPitch, durationSeconds = 1.0, velocity = 0.8, startTime = 0) {
        this.init();
        const now = startTime > 0 ? startTime : this.ctx.currentTime;
        const freq = this.midiToFreq(midiPitch);

        // Gain envelope for this note
        const noteGain = this.ctx.createGain();
        noteGain.connect(this.masterGain);

        // ADSR envelope: sharp hammer attack, smooth decay, release
        noteGain.gain.setValueAtTime(0, now);
        noteGain.gain.linearRampToValueAtTime(velocity * 0.9, now + 0.008); // Attack
        noteGain.gain.exponentialRampToValueAtTime(velocity * 0.4, now + 0.15); // Decay
        noteGain.gain.exponentialRampToValueAtTime(0.0001, now + Math.max(durationSeconds + 0.5, 0.6)); // Sustain & Release

        // Multi-harmonic oscillators (fundamental + overtones for realistic piano body)
        const harmonics = [
            { mult: 1.0, gain: 1.0 },
            { mult: 2.0, gain: 0.5 },
            { mult: 3.0, gain: 0.25 },
            { mult: 4.0, gain: 0.12 },
            { mult: 5.0, gain: 0.05 }
        ];

        harmonics.forEach(h => {
            const osc = this.ctx.createOscillator();
            osc.type = h.mult === 1.0 ? 'sine' : 'triangle';
            osc.frequency.setValueAtTime(freq * h.mult, now);

            const hGain = this.ctx.createGain();
            hGain.gain.value = h.gain;

            osc.connect(hGain);
            hGain.connect(noteGain);

            osc.start(now);
            osc.stop(now + durationSeconds + 0.6);
        });

        // Hammer transient click simulation
        const noiseBuffer = this.ctx.createBuffer(1, this.ctx.sampleRate * 0.015, this.ctx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < noiseBuffer.length; i++) {
            output[i] = (Math.random() * 2 - 1) * Math.exp(-i / (this.ctx.sampleRate * 0.003));
        }

        const noiseNode = this.ctx.createBufferSource();
        noiseNode.buffer = noiseBuffer;

        const noiseFilter = this.ctx.createBiquadFilter();
        noiseFilter.type = 'bandpass';
        noiseFilter.frequency.value = Math.min(freq * 3, 4000);
        noiseFilter.Q.value = 3.0;

        const noiseGain = this.ctx.createGain();
        noiseGain.gain.setValueAtTime(velocity * 0.3, now);
        noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.015);

        noiseNode.connect(noiseFilter);
        noiseFilter.connect(noiseGain);
        noiseGain.connect(noteGain);

        noiseNode.start(now);
        noiseNode.stop(now + 0.02);
    }

    playVocalNote(midiPitch, durationSeconds = 1.0, velocity = 0.85, startTime = 0) {
        this.init();
        const now = startTime > 0 ? startTime : this.ctx.currentTime;
        const dur = Math.max(0.06, durationSeconds);
        const freq = this.midiToFreq(midiPitch);

        const noteGain = this.ctx.createGain();
        noteGain.connect(this.masterGain);

        // Sustained vowel-like singing contour (holds full duration for pitch matching)
        const attack = Math.min(0.035, dur * 0.2);
        const release = Math.min(0.05, dur * 0.22);
        noteGain.gain.setValueAtTime(0.0001, now);
        noteGain.gain.linearRampToValueAtTime(velocity * 0.72, now + attack);
        noteGain.gain.setValueAtTime(velocity * 0.68, Math.max(now + attack, now + dur - release));
        noteGain.gain.exponentialRampToValueAtTime(0.0001, now + dur + 0.04);

        const formants = [
            { mult: 1.0, gain: 1.0, type: 'sine' },
            { mult: 2.0, gain: 0.42, type: 'sine' },
            { mult: 3.0, gain: 0.18, type: 'sine' },
            { mult: 4.0, gain: 0.06, type: 'triangle' }
        ];

        const lfo = this.ctx.createOscillator();
        const lfoGain = this.ctx.createGain();
        lfo.frequency.setValueAtTime(5.2, now);
        lfoGain.gain.setValueAtTime(dur > 0.35 ? freq * 0.0025 : 0.0, now);
        lfo.connect(lfoGain);

        formants.forEach(h => {
            const osc = this.ctx.createOscillator();
            osc.type = h.type;
            osc.frequency.setValueAtTime(freq * h.mult, now);
            lfoGain.connect(osc.frequency);

            const hGain = this.ctx.createGain();
            hGain.gain.value = h.gain;
            osc.connect(hGain);
            hGain.connect(noteGain);

            osc.start(now);
            osc.stop(now + dur + 0.06);
        });

        lfo.start(now);
        lfo.stop(now + dur + 0.06);
    }

    playLeadNote(midiPitch, durationSeconds = 1.0, velocity = 0.85, startTime = 0) {
        if (this.voiceMode === 'vocal_guide') {
            return this.playVocalNote(midiPitch, durationSeconds, velocity, startTime);
        }
        return this.playNote(midiPitch, durationSeconds, velocity, startTime);
    }

    playClick(accent = false, startTime = 0) {
        this.init();
        const now = startTime > 0 ? startTime : this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(accent ? 1280 : 880, now);
        gain.gain.setValueAtTime(accent ? 0.25 : 0.16, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.045);
        osc.connect(gain);
        gain.connect(this.masterGain);
        osc.start(now);
        osc.stop(now + 0.05);
    }
}

window.pianoSynth = new PianoSynthesizer();
