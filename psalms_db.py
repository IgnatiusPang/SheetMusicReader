import os
import json
from typing import Dict, List, Any

SCORES_DIR = os.path.join(os.path.dirname(__file__), "digitized_scores")

# Default high-fidelity digitized scores for the 5 attached psalm examples
DEFAULT_PSALMS: Dict[str, Dict[str, Any]] = {
    "psalm_119": {
        "id": "psalm_119",
        "title": "Ps 119(118) Lord I love your commands",
        "composer": "A Reefman",
        "key": "G Major",
        "key_signature": "1#",
        "time_signature": "2/2",
        "tempo": 90,
        "clef": "treble",
        "response": {
            "title": "Response",
            "chords": ["G/B", "C(add2)", "Bm7", "Cmaj7"],
            "notes": [
                {"pitch": "D4", "midi": 62, "duration": "quarter", "beats": 1.0, "lyric": "Lord,"},
                {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "I"},
                {"pitch": "B4", "midi": 71, "duration": "half", "beats": 2.0, "lyric": "love"},
                {"pitch": "A4", "midi": 69, "duration": "quarter", "beats": 1.0, "lyric": "your"},
                {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "com-"},
                {"pitch": "E4", "midi": 64, "duration": "half", "beats": 2.0, "lyric": "mands."},
                {"pitch": "F#4", "midi": 66, "duration": "half", "beats": 2.0, "lyric": ""},
                {"pitch": "G4", "midi": 67, "duration": "whole", "beats": 4.0, "lyric": ""}
            ],
            "accompaniment": [
                {"chord": "G/B", "bass_midi": 47, "chord_midis": [59, 62, 67], "beats": 2.0},
                {"chord": "C(add2)", "bass_midi": 48, "chord_midis": [60, 62, 64, 67], "beats": 2.0},
                {"chord": "Bm7", "bass_midi": 47, "chord_midis": [59, 62, 66, 69], "beats": 2.0},
                {"chord": "Cmaj7", "bass_midi": 48, "chord_midis": [60, 64, 67, 71], "beats": 4.0}
            ]
        },
        "verses": [
            {
                "verse_number": 1,
                "lyrics_text": "My part, I have resolved, O Lord, is to obey your word. The law from your mouth means more to me than silver and gold.",
                "notes": [
                    {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "My"},
                    {"pitch": "B4", "midi": 71, "duration": "quarter", "beats": 1.0, "lyric": "part,"},
                    {"pitch": "A4", "midi": 69, "duration": "quarter", "beats": 1.0, "lyric": "I"},
                    {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "have"},
                    {"pitch": "E4", "midi": 64, "duration": "quarter", "beats": 1.0, "lyric": "re-"},
                    {"pitch": "F#4", "midi": 66, "duration": "quarter", "beats": 1.0, "lyric": "solved,"},
                    {"pitch": "G4", "midi": 67, "duration": "half", "beats": 2.0, "lyric": "O"},
                    {"pitch": "A4", "midi": 69, "duration": "half", "beats": 2.0, "lyric": "Lord,"},
                    {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "is"},
                    {"pitch": "F#4", "midi": 66, "duration": "quarter", "beats": 1.0, "lyric": "to"},
                    {"pitch": "E4", "midi": 64, "duration": "quarter", "beats": 1.0, "lyric": "o-"},
                    {"pitch": "D4", "midi": 62, "duration": "quarter", "beats": 1.0, "lyric": "bey"},
                    {"pitch": "E4", "midi": 64, "duration": "quarter", "beats": 1.0, "lyric": "your"},
                    {"pitch": "G4", "midi": 67, "duration": "half", "beats": 2.0, "lyric": "word."}
                ],
                "chords": ["G(add2)", "/B", "C(add2)", "Cmaj7", "Em", "D(add2)", "C(#11)", "Am9"]
            },
            {
                "verse_number": 2,
                "lyrics_text": "Let your love be ready to console me by your promise to your servant. Let your love come and I shall live, for your law's my delight.",
                "notes": [
                    {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "Let"},
                    {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "your"},
                    {"pitch": "B4", "midi": 71, "duration": "quarter", "beats": 1.0, "lyric": "love"},
                    {"pitch": "A4", "midi": 69, "duration": "quarter", "beats": 1.0, "lyric": "be"},
                    {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "rea-"},
                    {"pitch": "F#4", "midi": 66, "duration": "quarter", "beats": 1.0, "lyric": "dy"},
                    {"pitch": "E4", "midi": 64, "duration": "quarter", "beats": 1.0, "lyric": "to"},
                    {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "con-"},
                    {"pitch": "A4", "midi": 69, "duration": "half", "beats": 2.0, "lyric": "sole"},
                    {"pitch": "G4", "midi": 67, "duration": "half", "beats": 2.0, "lyric": "me."}
                ],
                "chords": ["G(add2)", "/B", "C(add2)", "Cmaj7", "Em", "D(add2)", "C(#11)", "Am9"]
            }
        ]
    },
    "psalm_104": {
        "id": "psalm_104",
        "title": "Ps 104(103) Lord, send out Your Spirit",
        "composer": "A Reefman",
        "key": "E Major",
        "key_signature": "4#",
        "time_signature": "6/8",
        "tempo": 140,
        "clef": "treble",
        "response": {
            "title": "Response",
            "chords": ["E", "G#m7", "C#m7", "B", "A"],
            "notes": [
                {"pitch": "B3", "midi": 59, "duration": "eighth", "beats": 0.5, "lyric": "Lord,"},
                {"pitch": "E4", "midi": 64, "duration": "eighth", "beats": 0.5, "lyric": "send"},
                {"pitch": "E4", "midi": 64, "duration": "eighth", "beats": 0.5, "lyric": "out"},
                {"pitch": "G#4", "midi": 68, "duration": "eighth", "beats": 0.5, "lyric": "Your"},
                {"pitch": "G#4", "midi": 68, "duration": "eighth", "beats": 0.5, "lyric": "Spi-"},
                {"pitch": "F#4", "midi": 66, "duration": "eighth", "beats": 0.5, "lyric": "rit"},
                {"pitch": "E4", "midi": 64, "duration": "eighth", "beats": 0.5, "lyric": "and"},
                {"pitch": "G#4", "midi": 68, "duration": "eighth", "beats": 0.5, "lyric": "re-"},
                {"pitch": "B4", "midi": 71, "duration": "eighth", "beats": 0.5, "lyric": "new"},
                {"pitch": "B4", "midi": 71, "duration": "dotted_quarter", "beats": 1.5, "lyric": "the"},
                {"pitch": "A4", "midi": 69, "duration": "eighth", "beats": 0.5, "lyric": "face"},
                {"pitch": "G#4", "midi": 68, "duration": "eighth", "beats": 0.5, "lyric": "of"},
                {"pitch": "F#4", "midi": 66, "duration": "dotted_half", "beats": 3.0, "lyric": "the earth."}
            ],
            "accompaniment": [
                {"chord": "E", "bass_midi": 40, "chord_midis": [52, 64, 68, 71], "beats": 1.5},
                {"chord": "G#m7", "bass_midi": 44, "chord_midis": [56, 63, 68, 71], "beats": 1.5},
                {"chord": "C#m7", "bass_midi": 49, "chord_midis": [61, 64, 68, 71], "beats": 1.5},
                {"chord": "B", "bass_midi": 47, "chord_midis": [59, 63, 66, 71], "beats": 1.5},
                {"chord": "A", "bass_midi": 45, "chord_midis": [57, 64, 69, 73], "beats": 3.0}
            ]
        },
        "verses": [
            {
                "verse_number": 1,
                "lyrics_text": "Bless the Lord, my soul! Lord, God, how great You are, How many are Your works, O Lord! The earth is full of Your riches.",
                "notes": [
                    {"pitch": "E4", "midi": 64, "duration": "quarter", "beats": 1.0, "lyric": "Bless"},
                    {"pitch": "G#4", "midi": 68, "duration": "eighth", "beats": 0.5, "lyric": "the"},
                    {"pitch": "B4", "midi": 71, "duration": "quarter", "beats": 1.0, "lyric": "Lord,"},
                    {"pitch": "G#4", "midi": 68, "duration": "eighth", "beats": 0.5, "lyric": "my"},
                    {"pitch": "E4", "midi": 64, "duration": "dotted_quarter", "beats": 1.5, "lyric": "soul!"}
                ],
                "chords": ["B(sus4)", "B", "E", "C#m7", "/B", "A", "E/G#"]
            }
        ]
    },
    "psalm_23": {
        "id": "psalm_23",
        "title": "Psalm 23, 4th Sunday of Easter, Year A",
        "composer": "Aaron Reefman",
        "key": "C Major",
        "key_signature": "0",
        "time_signature": "6/8",
        "tempo": 110,
        "clef": "treble",
        "response": {
            "title": "Response",
            "chords": ["C", "/B", "Am", "/E", "F", "G", "C"],
            "notes": [
                {"pitch": "G3", "midi": 55, "duration": "eighth", "beats": 0.5, "lyric": "The"},
                {"pitch": "C4", "midi": 60, "duration": "dotted_quarter", "beats": 1.5, "lyric": "Lord"},
                {"pitch": "B3", "midi": 59, "duration": "eighth", "beats": 0.5, "lyric": "is"},
                {"pitch": "A3", "midi": 57, "duration": "dotted_quarter", "beats": 1.5, "lyric": "my"},
                {"pitch": "C4", "midi": 60, "duration": "eighth", "beats": 0.5, "lyric": "shep-"},
                {"pitch": "D4", "midi": 62, "duration": "eighth", "beats": 0.5, "lyric": "herd,"},
                {"pitch": "E4", "midi": 64, "duration": "eighth", "beats": 0.5, "lyric": "there"},
                {"pitch": "F4", "midi": 65, "duration": "eighth", "beats": 0.5, "lyric": "is"},
                {"pitch": "E4", "midi": 64, "duration": "eighth", "beats": 0.5, "lyric": "no-"},
                {"pitch": "D4", "midi": 62, "duration": "eighth", "beats": 0.5, "lyric": "thing"},
                {"pitch": "C4", "midi": 60, "duration": "eighth", "beats": 0.5, "lyric": "I"},
                {"pitch": "D4", "midi": 62, "duration": "eighth", "beats": 0.5, "lyric": "shall"},
                {"pitch": "C4", "midi": 60, "duration": "dotted_half", "beats": 3.0, "lyric": "want."}
            ],
            "accompaniment": [
                {"chord": "C", "bass_midi": 36, "chord_midis": [48, 60, 64, 67], "beats": 1.5},
                {"chord": "/B", "bass_midi": 47, "chord_midis": [59, 64, 67], "beats": 0.5},
                {"chord": "Am", "bass_midi": 45, "chord_midis": [57, 60, 64], "beats": 1.5},
                {"chord": "/E", "bass_midi": 40, "chord_midis": [52, 60, 64], "beats": 0.5},
                {"chord": "F", "bass_midi": 41, "chord_midis": [53, 60, 65, 69], "beats": 1.0},
                {"chord": "G", "bass_midi": 43, "chord_midis": [55, 59, 62, 67], "beats": 1.0},
                {"chord": "C", "bass_midi": 36, "chord_midis": [48, 60, 64, 67], "beats": 3.0}
            ]
        },
        "verses": [
            {
                "verse_number": 1,
                "lyrics_text": "The Lord is my shepherd there is nothing I shall want. Fresh and green are the pastures where He gives me repose.",
                "notes": [
                    {"pitch": "C4", "midi": 60, "duration": "eighth", "beats": 0.5, "lyric": "The"},
                    {"pitch": "E4", "midi": 64, "duration": "quarter", "beats": 1.0, "lyric": "Lord"},
                    {"pitch": "G4", "midi": 67, "duration": "eighth", "beats": 0.5, "lyric": "is"},
                    {"pitch": "A4", "midi": 69, "duration": "quarter", "beats": 1.0, "lyric": "my"},
                    {"pitch": "G4", "midi": 67, "duration": "eighth", "beats": 0.5, "lyric": "shep-"},
                    {"pitch": "E4", "midi": 64, "duration": "quarter", "beats": 1.0, "lyric": "herd"}
                ],
                "chords": ["F", "C/E", "Am", "G/B", "Dm", "G4", "G"]
            }
        ]
    },
    "psalm_130": {
        "id": "psalm_130",
        "title": "Ps 130(129) With the Lord there is Mercy",
        "composer": "A Reefman",
        "key": "D Major",
        "key_signature": "2#",
        "time_signature": "2/2",
        "tempo": 56,
        "clef": "treble",
        "response": {
            "title": "Response",
            "chords": ["A", "D", "/F#", "G", "A(sus4)", "A"],
            "notes": [
                {"pitch": "F#4", "midi": 66, "duration": "quarter", "beats": 1.0, "lyric": "With"},
                {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "the"},
                {"pitch": "A4", "midi": 69, "duration": "half", "beats": 2.0, "lyric": "Lord"},
                {"pitch": "F#4", "midi": 66, "duration": "quarter", "beats": 1.0, "lyric": "there"},
                {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "is"},
                {"pitch": "A4", "midi": 69, "duration": "quarter", "beats": 1.0, "lyric": "mer-"},
                {"pitch": "B4", "midi": 71, "duration": "quarter", "beats": 1.0, "lyric": "cy,"},
                {"pitch": "C#5", "midi": 73, "duration": "quarter", "beats": 1.0, "lyric": "and"},
                {"pitch": "D5", "midi": 74, "duration": "quarter", "beats": 1.0, "lyric": "full-"},
                {"pitch": "C#5", "midi": 73, "duration": "quarter", "beats": 1.0, "lyric": "ness"},
                {"pitch": "B4", "midi": 71, "duration": "quarter", "beats": 1.0, "lyric": "of"},
                {"pitch": "A4", "midi": 69, "duration": "half", "beats": 2.0, "lyric": "re-"},
                {"pitch": "G4", "midi": 67, "duration": "quarter", "beats": 1.0, "lyric": "dem-"},
                {"pitch": "F#4", "midi": 66, "duration": "whole", "beats": 4.0, "lyric": "ption."}
            ],
            "accompaniment": [
                {"chord": "A", "bass_midi": 45, "chord_midis": [57, 61, 64, 69], "beats": 2.0},
                {"chord": "D", "bass_midi": 50, "chord_midis": [62, 66, 69], "beats": 2.0},
                {"chord": "/F#", "bass_midi": 42, "chord_midis": [54, 62, 66], "beats": 2.0},
                {"chord": "G", "bass_midi": 43, "chord_midis": [55, 59, 62, 67], "beats": 2.0},
                {"chord": "A(sus4)", "bass_midi": 45, "chord_midis": [57, 62, 64, 69], "beats": 2.0},
                {"chord": "A", "bass_midi": 45, "chord_midis": [57, 61, 64, 69], "beats": 4.0}
            ]
        },
        "verses": [
            {
                "verse_number": 1,
                "lyrics_text": "Out of the depths I cry to you, O Lord, Lord hear my voice! O let your ears be attentive to the voice of my pleading.",
                "notes": [
                    {"pitch": "F#4", "midi": 66, "duration": "quarter", "beats": 1.0, "lyric": "Out"},
                    {"pitch": "F#4", "midi": 66, "duration": "quarter", "beats": 1.0, "lyric": "of"},
                    {"pitch": "A4", "midi": 69, "duration": "quarter", "beats": 1.0, "lyric": "the"},
                    {"pitch": "B4", "midi": 71, "duration": "half", "beats": 2.0, "lyric": "depths"}
                ],
                "chords": ["Bm", "F#m7", "G", "A", "F#", "Bm7/A", "D/F#", "C#ø7/E", "Em7", "A(sus4)"]
            }
        ]
    },
    "psalm_50": {
        "id": "psalm_50",
        "title": "Be Merciful Oh Lord (Ps. 50)",
        "composer": "Isaac Reefman",
        "key": "Ab Major",
        "key_signature": "4b",
        "time_signature": "4/4",
        "tempo": 80,
        "clef": "treble",
        "response": {
            "title": "Response",
            "chords": ["Fm", "Ab", "Db", "Eb", "Fm"],
            "notes": [
                {"pitch": "C4", "midi": 60, "duration": "half", "beats": 2.0, "lyric": "Be"},
                {"pitch": "Eb4", "midi": 63, "duration": "quarter", "beats": 1.0, "lyric": "mer-"},
                {"pitch": "F4", "midi": 65, "duration": "quarter", "beats": 1.0, "lyric": "ci-"},
                {"pitch": "Ab4", "midi": 68, "duration": "quarter", "beats": 1.0, "lyric": "ful,"},
                {"pitch": "Ab4", "midi": 68, "duration": "quarter", "beats": 1.0, "lyric": "oh"},
                {"pitch": "G4", "midi": 67, "duration": "half", "beats": 2.0, "lyric": "Lord,"},
                {"pitch": "F4", "midi": 65, "duration": "quarter", "beats": 1.0, "lyric": "for"},
                {"pitch": "Eb4", "midi": 63, "duration": "quarter", "beats": 1.0, "lyric": "we"},
                {"pitch": "F4", "midi": 65, "duration": "quarter", "beats": 1.0, "lyric": "have"},
                {"pitch": "Eb4", "midi": 63, "duration": "whole", "beats": 4.0, "lyric": "sinned."}
            ],
            "accompaniment": [
                {"chord": "Fm", "bass_midi": 41, "chord_midis": [53, 60, 65, 68], "beats": 2.0},
                {"chord": "Ab", "bass_midi": 44, "chord_midis": [56, 60, 63, 68], "beats": 2.0},
                {"chord": "Db", "bass_midi": 49, "chord_midis": [61, 65, 68], "beats": 2.0},
                {"chord": "Eb", "bass_midi": 51, "chord_midis": [63, 67, 70], "beats": 2.0},
                {"chord": "Fm", "bass_midi": 41, "chord_midis": [53, 60, 65, 68], "beats": 4.0}
            ]
        },
        "verses": [
            {
                "verse_number": 1,
                "lyrics_text": "Have mercy on me, oh God, in Your kindness. My offences, truly, I know them.",
                "notes": [
                    {"pitch": "C4", "midi": 60, "duration": "quarter", "beats": 1.0, "lyric": "Have"},
                    {"pitch": "Eb4", "midi": 63, "duration": "quarter", "beats": 1.0, "lyric": "mer-"},
                    {"pitch": "F4", "midi": 65, "duration": "half", "beats": 2.0, "lyric": "cy"}
                ],
                "chords": ["Fm", "Ab", "Db", "Eb"]
            }
        ]
    }
}

def ensure_scores_dir():
    os.makedirs(SCORES_DIR, exist_ok=True)
    # Save default digitized scores to JSON files if not present
    for psalm_id, psalm_data in DEFAULT_PSALMS.items():
        filepath = os.path.join(SCORES_DIR, f"{psalm_id}.json")
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(psalm_data, f, indent=2)

def list_psalms() -> List[Dict[str, Any]]:
    ensure_scores_dir()
    psalms = []
    for fname in sorted(os.listdir(SCORES_DIR)):
        if fname.endswith(".json"):
            filepath = os.path.join(SCORES_DIR, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                psalms.append({
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "composer": data.get("composer"),
                    "key": data.get("key"),
                    "time_signature": data.get("time_signature"),
                    "tempo": data.get("tempo")
                })
    return psalms

def get_psalm(psalm_id: str) -> Dict[str, Any]:
    ensure_scores_dir()
    filepath = os.path.join(SCORES_DIR, f"{psalm_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    elif psalm_id in DEFAULT_PSALMS:
        return DEFAULT_PSALMS[psalm_id]
    return {}

def save_psalm(psalm_data: Dict[str, Any]) -> str:
    ensure_scores_dir()
    psalm_id = psalm_data.get("id") or f"psalm_{len(os.listdir(SCORES_DIR)) + 1}"
    psalm_data["id"] = psalm_id
    filepath = os.path.join(SCORES_DIR, f"{psalm_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(psalm_data, f, indent=2)
    return psalm_id
