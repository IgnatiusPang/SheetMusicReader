document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const psalmSelect = document.getElementById('psalmSelect');
    const psalmSearchInput = document.getElementById('psalmSearchInput');
    const digitizeAllBtn = document.getElementById('digitizeAllBtn');
    const pdfInput = document.getElementById('pdfInput');
    const psalmTitle = document.getElementById('psalmTitle');
    const psalmKey = document.getElementById('psalmKey');
    const psalmTime = document.getElementById('psalmTime');
    const psalmTempoDisplay = document.getElementById('psalmTempoDisplay');
    
    const exportXmlBtn = document.getElementById('exportXmlBtn');
    const exportMidiBtn = document.getElementById('exportMidiBtn');
    const exportJsonBtn = document.getElementById('exportJsonBtn');
    
    const notesAndLyricsLayer = document.getElementById('notesAndLyricsLayer');
    const verseTabs = document.getElementById('verseTabs');
    const fullLyricsBox = document.getElementById('fullLyricsBox');
    
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    const accompanimentToggle = document.getElementById('accompanimentToggle');
    const tempoSlider = document.getElementById('tempoSlider');
    const tempoValue = document.getElementById('tempoValue');
    const transposeSelect = document.getElementById('transposeSelect');
    
    const statusIndicator = document.getElementById('statusIndicator');
    const pianoKeyboard = document.getElementById('pianoKeyboard');

    // App State
    let allPsalmsList = [];
    let currentPsalm = null;
    let isPlaying = false;
    let isPaused = false;
    let playbackTimeout = null;
    let playbackIndex = 0;

    // Note Names for 61-key Keyboard Generation (C2 to C7)
    const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

    // Calculate vertical diatonic staff step relative to E4 (step 0 = bottom staff line)
    function getDiatonicStep(pitchStr, midiVal) {
        const stepLetters = { 'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6 };
        let letter = 'E';
        let octave = 4;
        
        if (pitchStr && pitchStr.length >= 2) {
            letter = pitchStr[0].toUpperCase();
            const m = pitchStr.match(/\d+/);
            if (m) octave = parseInt(m[0], 10);
        } else if (midiVal) {
            const midiLetters = ['C', 'C', 'D', 'D', 'E', 'F', 'F', 'G', 'G', 'A', 'A', 'B'];
            letter = midiLetters[midiVal % 12];
            octave = Math.floor(midiVal / 12) - 1;
        }
        
        const diatonicIndex = octave * 7 + (stepLetters[letter] !== undefined ? stepLetters[letter] : 2);
        const E4_index = 30; // 4 * 7 + 2 = 30
        return diatonicIndex - E4_index;
    }

    function shouldShowAccidental(pitch, keyName) {
        if (!pitch) return false;
        const isSharp = pitch.includes('#') || pitch.includes('♯');
        const isFlat = pitch.includes('b') || pitch.includes('♭');
        if (!isSharp && !isFlat) return false;

        const letter = pitch[0].toUpperCase();
        
        const keyFlats = {
            'F Major': ['B'],
            'Bb Major': ['B', 'E'],
            'Eb Major': ['B', 'E', 'A'],
            'Ab Major': ['B', 'E', 'A', 'D'],
            'Db Major': ['B', 'E', 'A', 'D', 'G'],
            'Gb Major': ['B', 'E', 'A', 'D', 'G', 'C']
        };
        
        const keySharps = {
            'G Major': ['F'],
            'D Major': ['F', 'C'],
            'A Major': ['F', 'C', 'G'],
            'E Major': ['F', 'C', 'G', 'D'],
            'B Major': ['F', 'C', 'G', 'D', 'A']
        };

        if (isFlat && keyFlats[keyName] && keyFlats[keyName].includes(letter)) return false;
        if (isSharp && keySharps[keyName] && keySharps[keyName].includes(letter)) return false;

        return true;
    }

    // 1. Initialize Piano Keyboard Visualizer (61 Keys: MIDI 36 to 96)
    function buildPianoKeyboard() {
        pianoKeyboard.innerHTML = '';
        const START_MIDI = 36; // C2
        const END_MIDI = 96;   // C7
        
        let whiteKeyOffset = 0;
        const keyWidth = 32;

        for (let midi = START_MIDI; midi <= END_MIDI; midi++) {
            const noteIndex = midi % 12;
            const octave = Math.floor(midi / 12) - 1;
            const noteName = NOTE_NAMES[noteIndex] + octave;
            const isBlack = NOTE_NAMES[noteIndex].includes('#');

            const keyEl = document.createElement('div');
            keyEl.setAttribute('data-midi', midi);
            keyEl.setAttribute('data-note', noteName);
            keyEl.setAttribute('data-testid', `key-${noteName}`);

            if (isBlack) {
                keyEl.className = 'black-key';
                keyEl.style.left = `${(whiteKeyOffset - 1) * keyWidth + 21}px`;
            } else {
                keyEl.className = 'white-key';
                keyEl.style.left = `${whiteKeyOffset * keyWidth}px`;
                keyEl.innerText = noteIndex === 0 ? noteName : '';
                whiteKeyOffset++;
            }

            keyEl.addEventListener('mousedown', () => {
                const transpose = parseInt(transposeSelect.value, 10) || 0;
                window.pianoSynth.playNote(midi + transpose, 1.0, 0.85);
                highlightKey(midi + transpose, true);
                setTimeout(() => highlightKey(midi + transpose, false), 300);
            });

            pianoKeyboard.appendChild(keyEl);
        }
    }

    function highlightKey(midiPitch, active) {
        const keyEl = pianoKeyboard.querySelector(`[data-midi="${midiPitch}"]`);
        if (keyEl) {
            if (active) {
                keyEl.classList.add('active');
                keyEl.setAttribute('data-active', 'true');
            } else {
                keyEl.classList.remove('active');
                keyEl.removeAttribute('data-active');
            }
        }
    }

    function clearAllHighlightedKeys() {
        const activeKeys = pianoKeyboard.querySelectorAll('.active');
        activeKeys.forEach(k => {
            k.classList.remove('active');
            k.removeAttribute('data-active');
        });
    }

    // 2. Fetch Psalm List
    async function loadPsalmList(filterQuery = '') {
        try {
            const res = await fetch('/api/psalms');
            const data = await res.json();
            allPsalmsList = data.psalms || [];
            
            renderPsalmSelectOptions(filterQuery);

            if (allPsalmsList.length > 0 && !currentPsalm) {
                loadPsalmDetail(allPsalmsList[0].id);
            }
        } catch (err) {
            statusIndicator.innerText = 'Status: Error loading psalm list';
        }
    }

    function renderPsalmSelectOptions(filterQuery = '') {
        const query = filterQuery.toLowerCase().trim();
        psalmSelect.innerHTML = '';
        
        const filtered = allPsalmsList.filter(p => 
            !query || 
            p.title.toLowerCase().includes(query) || 
            p.id.toLowerCase().includes(query)
        );

        if (filtered.length === 0) {
            const opt = document.createElement('option');
            opt.disabled = true;
            opt.innerText = 'No Psalms match search';
            psalmSelect.appendChild(opt);
            return;
        }

        filtered.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.innerText = p.title;
            if (currentPsalm && currentPsalm.id === p.id) {
                opt.selected = true;
            }
            psalmSelect.appendChild(opt);
        });
    }

    // 3. Fetch & Render Psalm Detail
    async function loadPsalmDetail(psalmId) {
        stopPlayback();
        statusIndicator.innerText = `Status: Loading ${psalmId}...`;
        try {
            const res = await fetch(`/api/psalms/${psalmId}`);
            const data = await res.json();
            currentPsalm = data;
            
            psalmTitle.innerText = data.title;
            psalmKey.innerText = `Key: ${data.key}`;
            psalmTime.innerText = `Time: ${data.time_signature}`;
            psalmTempoDisplay.innerText = `BPM: ${data.tempo}`;
            
            tempoSlider.value = data.tempo;
            tempoValue.innerText = data.tempo;

            renderClefSidebar(data);
            renderScoreNotation(data);
            renderVerseTabs(data);
            statusIndicator.innerText = 'Status: Ready';
        } catch (err) {
            statusIndicator.innerText = 'Status: Error loading score';
        }
    }

    function renderClefSidebar(data) {
        const clefKeySig = document.getElementById('clefKeySig');
        const timeSigEl = document.getElementById('clefTimeSig');
        const notesLayer = document.getElementById('notesAndLyricsLayer');
        const barLineEl = document.querySelector('.staff-header-bar-line');
        if (!clefKeySig) return;

        const keySig = data.key_signature || '0';
        let sigHtml = '';

        // Standard Treble Staff Line Y Offsets (top line F5 is y = 40px)
        const sharpOffsets = [30, 48, 24, 42, 60, 36, 54]; // F#, C#, G#, D#, A#, E#, B#
        const flatOffsets  = [46, 28, 52, 34, 58, 40, 64]; // Bb, Eb, Ab, Db, Gb, Cb, Fb

        let keyWidth = 0;

        if (keySig.includes('#')) {
            const count = Math.min(7, parseInt(keySig) || 1);
            keyWidth = count * 12;
            sigHtml = `<div class="key-sig-staff-wrapper" style="width: ${keyWidth}px;">`;
            for (let i = 0; i < count; i++) {
                const topPx = sharpOffsets[i];
                sigHtml += `<span class="sig-accidental sharp" style="top: ${topPx}px; left: ${i * 12}px;">♯</span>`;
            }
            sigHtml += '</div>';
        } else if (keySig.includes('b')) {
            const count = Math.min(7, parseInt(keySig) || 1);
            keyWidth = count * 12;
            sigHtml = `<div class="key-sig-staff-wrapper" style="width: ${keyWidth}px;">`;
            for (let i = 0; i < count; i++) {
                const topPx = flatOffsets[i];
                sigHtml += `<span class="sig-accidental flat" style="top: ${topPx}px; left: ${i * 12}px;">♭</span>`;
            }
            sigHtml += '</div>';
        } else {
            sigHtml = '';
            keyWidth = 0;
        }

        clefKeySig.innerHTML = sigHtml;

        const keyLeft = 65;
        clefKeySig.style.left = `${keyLeft}px`;

        let timeLeft = keyLeft + keyWidth + (keyWidth > 0 ? 8 : 0);
        if (timeSigEl) {
            const ts = data.time_signature || '4/4';
            const parts = ts.split('/');
            if (parts.length === 2) {
                timeSigEl.style.left = `${timeLeft}px`;
                timeSigEl.innerHTML = `<div class="time-sig-stacked"><span class="top-num">${parts[0]}</span><span class="bot-num">${parts[1]}</span></div>`;
            }
        }

        const barLeft = timeLeft + 28;
        if (barLineEl) {
            barLineEl.style.left = `${barLeft}px`;
        }

        if (notesLayer) {
            notesLayer.style.paddingLeft = `${barLeft + 15}px`;
        }
    }

    // 4. Render Staff Notation with Accurate Notehead Staff Positions, Rests & Overlaid Lyrics
    function renderScoreNotation(psalmData) {
        notesAndLyricsLayer.innerHTML = '';
        const notes = psalmData.response ? psalmData.response.notes : [];
        const chords = psalmData.response ? psalmData.response.chords : [];
        const keyName = psalmData.key || 'C Major';

        notes.forEach((note, idx) => {
            const item = document.createElement('div');
            item.className = 'note-item';
            item.setAttribute('data-index', idx);
            item.setAttribute('data-testid', `note-item-${idx}`);

            // Chord Annotation above note
            const chordEl = document.createElement('div');
            chordEl.className = 'chord-annotation';
            chordEl.innerText = (idx < chords.length && idx % 2 === 0) ? chords[idx / 2] : '';

            // Calculate vertical staff placement
            const step = getDiatonicStep(note.pitch, note.midi);
            const headTop = 43 - (step * 6);

            const graphicEl = document.createElement('div');
            graphicEl.className = 'note-graphic';

            const duration = note.duration || 'quarter';

            if (note.rest || note.is_rest) {
                // High-Definition Musical Rest SVG Symbols (Quarter 𝄽, Half 𝄼, Whole 𝄻, Eighth 𝄾)
                const restEl = document.createElement('div');
                restEl.className = 'rest-symbol';
                restEl.setAttribute('data-testid', `rest-symbol-${idx}`);

                if (duration === 'half') {
                    // Half Rest: Rectangle sitting on staff line 3 (B4)
                    restEl.innerHTML = `<svg width="24" height="24" viewBox="0 0 40 40" fill="#00F2FE" style="position: absolute; top: 16px; left: 10px;"><rect x="8" y="14" width="24" height="8" rx="1"/><line x1="4" y1="22" x2="36" y2="22" stroke="#00F2FE" stroke-width="2"/></svg>`;
                } else if (duration === 'whole') {
                    // Whole Rest: Rectangle hanging under staff line 4 (D5)
                    restEl.innerHTML = `<svg width="24" height="24" viewBox="0 0 40 40" fill="#00F2FE" style="position: absolute; top: 10px; left: 10px;"><rect x="8" y="10" width="24" height="8" rx="1"/><line x1="4" y1="10" x2="36" y2="10" stroke="#00F2FE" stroke-width="2"/></svg>`;
                } else if (duration === 'eighth') {
                    // Eighth Rest: Curved flag hook
                    restEl.innerHTML = `<svg width="20" height="38" viewBox="0 0 30 50" fill="#00F2FE" style="position: absolute; top: 14px; left: 12px;"><circle cx="10" cy="14" r="4"/><path d="M 10 14 Q 18 16 16 26 L 10 44" stroke="#00F2FE" stroke-width="3" fill="none"/></svg>`;
                } else {
                    // Quarter Rest (𝄽): Z-curve centered on staff line 3
                    restEl.innerHTML = `<svg width="22" height="42" viewBox="0 0 30 60" fill="#00F2FE" style="position: absolute; top: 10px; left: 11px;"><path d="M 12 5 C 18 10 22 18 16 26 C 14 29 10 32 16 38 C 20 42 22 48 18 54 C 15 58 10 57 12 52 C 14 47 11 44 8 40 C 4 35 6 28 10 24 C 14 20 10 12 8 8 Z"/></svg>`;
                }
                graphicEl.appendChild(restEl);
            } else {
                // Note Head & Stem Graphic
                const headEl = document.createElement('div');
                const isHollow = duration.includes('half') || duration === 'whole';
                headEl.className = `note-head ${isHollow ? 'hollow' : ''}`;
                headEl.style.top = `${headTop}px`;
                headEl.setAttribute('data-midi', note.midi);
                headEl.setAttribute('data-pitch', note.pitch);

                if (duration.includes('dotted')) {
                    const dot = document.createElement('span');
                    dot.className = 'augmentation-dot';
                    headEl.appendChild(dot);
                }

                if (shouldShowAccidental(note.pitch, keyName)) {
                    const accEl = document.createElement('span');
                    accEl.className = 'accidental-mark';
                    accEl.innerText = note.pitch.includes('#') ? '♯' : '♭';
                    headEl.appendChild(accEl);
                }

                if (step <= -2) {
                    const ledger = document.createElement('div');
                    ledger.className = 'ledger-line';
                    headEl.appendChild(ledger);
                }

                if (duration !== 'whole') {
                    const stemEl = document.createElement('div');
                    if (step >= 4) {
                        stemEl.className = 'stem-down';
                        stemEl.style.top = `${headTop + 5}px`;
                    } else {
                        stemEl.className = 'stem-up';
                        stemEl.style.top = `${headTop - 26}px`;
                        if (duration === 'eighth') {
                            const flag = document.createElement('div');
                            flag.className = 'stem-flag-up';
                            stemEl.appendChild(flag);
                        }
                    }
                    graphicEl.appendChild(stemEl);
                }

                graphicEl.appendChild(headEl);
            }

            // Overlaid Lyric Syllable directly underneath note head
            const lyricEl = document.createElement('div');
            lyricEl.className = 'lyric-syllable';
            lyricEl.innerText = note.lyric || '';
            lyricEl.setAttribute('data-testid', `lyric-word-${idx}`);

            item.appendChild(chordEl);
            item.appendChild(graphicEl);
            item.appendChild(lyricEl);

            item.addEventListener('click', () => {
                if (!note.rest && !note.is_rest) {
                    const transpose = parseInt(transposeSelect.value, 10) || 0;
                    window.pianoSynth.playNote(note.midi + transpose, 0.8, 0.9);
                    highlightKey(note.midi + transpose, true);
                    setTimeout(() => highlightKey(note.midi + transpose, false), 300);
                }
                highlightNoteAndLyric(idx);
                setTimeout(() => clearNoteHighlight(idx), 300);
            });

            notesAndLyricsLayer.appendChild(item);
        });

        renderBeamsSvg(notes);
        renderTiesSvg(notes);
    }

    // Render horizontal beam bars joining consecutive note stems in beat pairs (first pair, second pair)
    function renderBeamsSvg(notes) {
        let svg = notesAndLyricsLayer.querySelector('.beams-layer-svg');
        if (!svg) {
            svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svg.className = 'beams-layer-svg';
            svg.setAttribute('style', 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 9;');
            notesAndLyricsLayer.appendChild(svg);
        }
        svg.innerHTML = '';

        const noteItems = notesAndLyricsLayer.querySelectorAll('.note-item');
        const isBeamedDuration = (n) => n && !n.rest && !n.is_rest && (n.duration === 'eighth' || n.duration === 'sixteenth' || (n.beats && n.beats <= 0.5));

        let i = 0;
        while (i < notes.length - 1) {
            const note1 = notes[i];
            const note2 = notes[i + 1];

            if (isBeamedDuration(note1) && isBeamedDuration(note2)) {
                const item1 = noteItems[i];
                const item2 = noteItems[i + 1];
                if (item1 && item2) {
                    const step1 = getDiatonicStep(note1.pitch, note1.midi);
                    const headTop1 = 43 - (step1 * 6);
                    const step2 = getDiatonicStep(note2.pitch, note2.midi);
                    const headTop2 = 43 - (step2 * 6);

                    const x1 = item1.offsetLeft + 32;
                    const y1 = 40 + headTop1 - 25;

                    const x2 = item2.offsetLeft + 32;
                    const y2 = 40 + headTop2 - 25;

                    // Draw 5px thick horizontal stem beam bar joining pair 1 and pair 2
                    const beam = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                    beam.setAttribute("points", `${x1},${y1} ${x2},${y2} ${x2},${y2 + 5} ${x1},${y1 + 5}`);
                    beam.setAttribute("fill", "#00F2FE");
                    beam.setAttribute("opacity", "0.95");
                    svg.appendChild(beam);
                }
                // Skip 2 to beam in discrete pairs (first pair, then second pair)
                i += 2;
            } else {
                i += 1;
            }
        }
    }

    // Render authentic filled musical tie arc symbol bridging the two noteheads
    function renderTiesSvg(notes) {
        let svg = notesAndLyricsLayer.querySelector('.ties-layer-svg');
        if (!svg) {
            svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svg.className = 'ties-layer-svg';
            svg.setAttribute('style', 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 10;');
            notesAndLyricsLayer.appendChild(svg);
        }
        svg.innerHTML = '';

        const noteItems = notesAndLyricsLayer.querySelectorAll('.note-item');
        notes.forEach((note, idx) => {
            if ((note.tie === 'start' || note.tied) && idx + 1 < noteItems.length) {
                const item1 = noteItems[idx];
                const item2 = noteItems[idx + 1];

                const nextNote = notes[idx + 1];

                const step1 = getDiatonicStep(note.pitch, note.midi);
                const headTop1 = 43 - (step1 * 6);
                
                const step2 = getDiatonicStep(nextNote.pitch, nextNote.midi);
                const headTop2 = 43 - (step2 * 6);

                const x1 = item1.offsetLeft + 24;
                const y1 = 40 + headTop1 + 13;

                const x2 = item2.offsetLeft + 24;
                const y2 = 40 + headTop2 + 13;

                const xc = (x1 + x2) / 2;
                const yc1 = Math.max(y1, y2) + 14;
                const yc2 = Math.max(y1, y2) + 18;

                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                path.setAttribute("d", `M ${x1} ${y1} Q ${xc} ${yc2} ${x2} ${y2} Q ${xc} ${yc1} ${x1} ${y1} Z`);
                path.setAttribute("fill", "#00F2FE");
                path.setAttribute("opacity", "0.95");
                svg.appendChild(path);
            }
        });
    }

    function renderVerseTabs(psalmData) {
        verseTabs.innerHTML = '';
        
        const respTab = document.createElement('button');
        respTab.className = 'verse-tab active';
        respTab.innerText = 'Response';
        respTab.setAttribute('data-verse', '0');
        respTab.addEventListener('click', () => selectVerseTab(0));
        verseTabs.appendChild(respTab);

        if (psalmData.verses) {
            psalmData.verses.forEach((v, idx) => {
                const tab = document.createElement('button');
                tab.className = 'verse-tab';
                tab.innerText = `Verse ${v.verse_number || idx + 1}`;
                tab.setAttribute('data-verse', idx + 1);
                tab.addEventListener('click', () => selectVerseTab(idx + 1));
                verseTabs.appendChild(tab);
            });
        }

        fullLyricsBox.innerHTML = `<p class="lyrics-text">${psalmData.response ? psalmData.response.notes.map(n=>n.lyric).join(' ') : ''}</p>`;
    }

    function selectVerseTab(index) {
        const tabs = verseTabs.querySelectorAll('.verse-tab');
        tabs.forEach(t => t.classList.remove('active'));
        if (tabs[index]) tabs[index].classList.add('active');

        if (index === 0 && currentPsalm && currentPsalm.response) {
            renderScoreNotation(currentPsalm);
            fullLyricsBox.innerHTML = `<p class="lyrics-text">${currentPsalm.response.notes.map(n=>n.lyric).join(' ')}</p>`;
        } else if (currentPsalm && currentPsalm.verses && currentPsalm.verses[index - 1]) {
            const verse = currentPsalm.verses[index - 1];
            notesAndLyricsLayer.innerHTML = '';
            
            const notes = verse.notes || currentPsalm.response.notes || [];
            const keyName = currentPsalm.key || 'C Major';

            notes.forEach((n, idx) => {
                const item = document.createElement('div');
                item.className = 'note-item';
                item.setAttribute('data-index', idx);

                const step = getDiatonicStep(n.pitch, n.midi);
                const headTop = 43 - (step * 6);

                const graphicEl = document.createElement('div');
                graphicEl.className = 'note-graphic';
                const duration = n.duration || 'quarter';

                if (n.rest || n.is_rest) {
                    const restEl = document.createElement('div');
                    restEl.className = 'rest-symbol';
                    restEl.style.top = '18px';
                    restEl.innerText = duration === 'half' ? '𝄼' : duration === 'whole' ? '𝄻' : duration === 'eighth' ? '𝄾' : '𝄽';
                    graphicEl.appendChild(restEl);
                } else {
                    const headEl = document.createElement('div');
                    const isHollow = duration.includes('half') || duration === 'whole';
                    headEl.className = `note-head ${isHollow ? 'hollow' : ''}`;
                    headEl.style.top = `${headTop}px`;

                    if (duration.includes('dotted')) {
                        const dot = document.createElement('span');
                        dot.className = 'augmentation-dot';
                        headEl.appendChild(dot);
                    }

                    if (shouldShowAccidental(n.pitch, keyName)) {
                        const accEl = document.createElement('span');
                        accEl.className = 'accidental-mark';
                        accEl.innerText = n.pitch.includes('#') ? '♯' : '♭';
                        headEl.appendChild(accEl);
                    }

                    if (duration !== 'whole') {
                        const stemEl = document.createElement('div');
                        if (step >= 4) {
                            stemEl.className = 'stem-down';
                            stemEl.style.top = `${headTop + 5}px`;
                        } else {
                            stemEl.className = 'stem-up';
                            stemEl.style.top = `${headTop - 26}px`;
                            if (duration === 'eighth') {
                                const flag = document.createElement('div');
                                flag.className = 'stem-flag-up';
                                stemEl.appendChild(flag);
                            }
                        }
                        graphicEl.appendChild(stemEl);
                    }

                    graphicEl.appendChild(headEl);
                }

                const lyricEl = document.createElement('div');
                lyricEl.className = 'lyric-syllable';
                lyricEl.innerText = n.lyric || '';

                item.appendChild(graphicEl);
                item.appendChild(lyricEl);
                notesAndLyricsLayer.appendChild(item);
            });
            
            renderTiesSvg(notes);
            fullLyricsBox.innerHTML = `<p class="lyrics-text">${verse.lyrics_text || ''}</p>`;
        }
    }

    function highlightNoteAndLyric(index) {
        const items = notesAndLyricsLayer.querySelectorAll('.note-item');
        items.forEach(i => i.classList.remove('active'));
        if (items[index]) {
            items[index].classList.add('active');
            items[index].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
    }

    function clearNoteHighlight(index) {
        const items = notesAndLyricsLayer.querySelectorAll('.note-item');
        if (items[index]) {
            items[index].classList.remove('active');
        }
    }

    // 5. Audio Playback Engine
    function startPlayback() {
        if (!currentPsalm || !currentPsalm.response) return;
        isPlaying = true;
        isPaused = false;
        playBtn.disabled = true;
        pauseBtn.disabled = false;
        stopBtn.disabled = false;
        statusIndicator.innerText = 'Status: Playing Melody...';

        playNextStep();
    }

    function playNextStep() {
        if (!isPlaying || isPaused || !currentPsalm) return;

        const notes = currentPsalm.response.notes || [];
        const accompaniment = currentPsalm.response.accompaniment || [];
        const bpm = parseInt(tempoSlider.value, 10) || 90;
        const secondsPerBeat = 60.0 / bpm;
        const transpose = parseInt(transposeSelect.value, 10) || 0;

        if (playbackIndex >= notes.length) {
            stopPlayback();
            statusIndicator.innerText = 'Status: Playback Finished';
            return;
        }

        const note = notes[playbackIndex];
        let durBeats = note.beats || 1.0;

        // Silent Rest Handling
        if (note.rest || note.is_rest) {
            clearAllHighlightedKeys();
            highlightNoteAndLyric(playbackIndex);
            playbackIndex++;
            playbackTimeout = setTimeout(() => {
                clearAllHighlightedKeys();
                playNextStep();
            }, durBeats * secondsPerBeat * 1000);
            return;
        }
        
        // If this note is tied to the next note, sustain across both notes!
        let isTiedStart = false;
        if (note.tie === 'start' && playbackIndex + 1 < notes.length) {
            const nextNote = notes[playbackIndex + 1];
            durBeats += (nextNote.beats || 1.0);
            isTiedStart = true;
        } else if (note.tie === 'stop') {
            clearAllHighlightedKeys();
            highlightNoteAndLyric(playbackIndex);
            playbackIndex++;
            playbackTimeout = setTimeout(() => {
                clearAllHighlightedKeys();
                playNextStep();
            }, durBeats * secondsPerBeat * 1000);
            return;
        }

        const durationSeconds = durBeats * secondsPerBeat;
        const pitch = note.midi + transpose;

        // Play Top Melody Note
        window.pianoSynth.playNote(pitch, durationSeconds, 0.9);

        // Play Accompaniment Chords if toggled ON
        if (accompanimentToggle.checked && playbackIndex < accompaniment.length) {
            const accItem = accompaniment[playbackIndex];
            if (accItem.chord_midis) {
                accItem.chord_midis.forEach(m => {
                    window.pianoSynth.playNote(m + transpose, durationSeconds * 0.9, 0.45);
                });
            }
            if (accItem.bass_midi) {
                window.pianoSynth.playNote(accItem.bass_midi + transpose, durationSeconds, 0.6);
            }
        }

        // Highlight active note, lyric, and keyboard visualizer key
        clearAllHighlightedKeys();
        highlightNoteAndLyric(playbackIndex);
        highlightKey(pitch, true);

        playbackIndex++;
        playbackTimeout = setTimeout(() => {
            clearAllHighlightedKeys();
            playNextStep();
        }, durationSeconds * 1000);
    }

    function pausePlayback() {
        isPlaying = false;
        isPaused = true;
        clearTimeout(playbackTimeout);
        playBtn.disabled = false;
        pauseBtn.disabled = true;
        statusIndicator.innerText = 'Status: Paused';
    }

    function stopPlayback() {
        isPlaying = false;
        isPaused = false;
        clearTimeout(playbackTimeout);
        playbackIndex = 0;
        playBtn.disabled = false;
        pauseBtn.disabled = true;
        stopBtn.disabled = true;
        clearAllHighlightedKeys();
        const items = notesAndLyricsLayer.querySelectorAll('.note-item');
        items.forEach(i => i.classList.remove('active'));
        statusIndicator.innerText = 'Status: Stopped';
    }

    // 6. Export Handlers
    exportXmlBtn.addEventListener('click', () => {
        if (!currentPsalm) return;
        window.open(`/api/psalms/${currentPsalm.id}/export/musicxml`, '_blank');
    });

    exportMidiBtn.addEventListener('click', () => {
        if (!currentPsalm) return;
        window.open(`/api/psalms/${currentPsalm.id}/export/midi`, '_blank');
    });

    exportJsonBtn.addEventListener('click', () => {
        if (!currentPsalm) return;
        window.open(`/api/psalms/${currentPsalm.id}/export/json`, '_blank');
    });

    // 7. Event Listeners
    psalmSelect.addEventListener('change', (e) => loadPsalmDetail(e.target.value));

    if (psalmSearchInput) {
        psalmSearchInput.addEventListener('input', (e) => {
            renderPsalmSelectOptions(e.target.value);
            if (psalmSelect.options.length > 0 && psalmSelect.options[0].value) {
                psalmSelect.selectedIndex = 0;
                loadPsalmDetail(psalmSelect.value);
            }
        });
    }

    if (digitizeAllBtn) {
        digitizeAllBtn.addEventListener('click', async () => {
            statusIndicator.innerText = 'Status: Batch digitizing all Psalm PDFs...';
            try {
                const res = await fetch('/api/digitize-all', { method: 'POST' });
                const data = await res.json();
                await loadPsalmList();
                statusIndicator.innerText = `Status: ${data.message || 'Digitized All PDFs successfully'}`;
            } catch (err) {
                statusIndicator.innerText = 'Status: Error digitizing PDFs';
            }
        });
    }
    
    playBtn.addEventListener('click', startPlayback);
    pauseBtn.addEventListener('click', pausePlayback);
    stopBtn.addEventListener('click', stopPlayback);
    
    tempoSlider.addEventListener('input', (e) => {
        tempoValue.innerText = e.target.value;
        if (currentPsalm) psalmTempoDisplay.innerText = `BPM: ${e.target.value}`;
    });

    pdfInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        statusIndicator.innerText = `Status: Digitizing ${file.name}...`;
        const formData = new FormData();
        formData.append('pdf', file);

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.psalm) {
                await loadPsalmList();
                psalmSelect.value = data.psalm.id;
                loadPsalmDetail(data.psalm.id);
                statusIndicator.innerText = `Status: Uploaded & Digitized ${file.name}`;
            }
        } catch (err) {
            statusIndicator.innerText = 'Status: Error uploading PDF';
        }
    });

    // Init App
    buildPianoKeyboard();
    loadPsalmList();
});
