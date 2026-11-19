import os
import tempfile
from itertools import chain
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response
import psalms_db
import score_formatter
import pdf_parser
import digitize_all
import lean_bridge
import vector_omr
import karaoke_trainer
from music_pipeline import FIFTHS_TO_KEY_NAME

app = Flask(__name__, template_folder="templates", static_folder="static")
DATA_DIR = Path(__file__).resolve().parent / "data"

# Ensure default and digitized scores are loaded
psalms_db.ensure_scores_dir()


def _list_karaoke_sources() -> list[dict]:
    """List PDF and digitized scores available for the interactive Karaoke Trainer."""
    pdfs = (
        sorted(
            DATA_DIR.glob("*.pdf"),
            key=lambda p: (0 if p.name == "Ps-122-I-Rejoiced-Chart.pdf" else 1, p.name.lower()),
        )
        if DATA_DIR.is_dir()
        else ()
    )
    pdf_items = map(
        lambda p: {
            "id": f"pdf:{p.name}",
            "label": f"📄 {p.stem.replace('-', ' ')}",
            "title": p.stem.replace("-", " "),
            "source_type": "pdf",
            "filename": p.name,
        },
        pdfs,
    )
    psalm_items = map(
        lambda p: {
            "id": f"psalm:{p['id']}",
            "label": f"🎼 {p.get('title', p['id'])}",
            "title": p.get("title", p["id"]),
            "source_type": "psalm",
            "key": p.get("key"),
            "time_signature": p.get("time_signature"),
        },
        psalms_db.list_psalms(),
    )
    return [*pdf_items, *psalm_items]


def _parse_bool_arg(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return str(raw).strip().lower() not in ("0", "false", "no", "off")


def _parse_export_params() -> tuple[float, int, str, int, bool, bool]:
    try:
        speed = float(request.args.get("speed", "1.0"))
    except ValueError:
        speed = 1.0
    speed = max(0.05, min(4.0, speed))
    try:
        augment = int(request.args.get("augment", "1"))
    except ValueError:
        augment = 1
    augment = max(1, min(8, augment))
    voice = str(request.args.get("voice", "vocal_guide")).strip().lower()
    try:
        count_in = max(0, min(4, int(request.args.get("count_in", "1"))))
    except ValueError:
        count_in = 1
    clicks = _parse_bool_arg(request.args.get("clicks"), True)
    accompaniment = _parse_bool_arg(request.args.get("accompaniment"), True)
    return speed, augment, voice, count_in, clicks, accompaniment


def _vector_fallback_notes(score: vector_omr.Score) -> dict | None:
    """Build score metadata and notes from vector_omr when pdf_parser has no metadata preset."""
    if not getattr(score, "systems", None):
        return None
    sp = lean_bridge.spec_from_vector_score(score, lane=0)
    if not sp.bars:
        return None
    first_sys = score.systems[0]
    first_m = first_sys[0].measures[0] if first_sys and first_sys[0].measures else None
    fifths = int(first_m.key) if first_m is not None else 0
    key_name = FIFTHS_TO_KEY_NAME.get(fifths, "C Major")
    key_sig = f"{fifths}#" if fifths > 0 else (f"{abs(fifths)}b" if fifths < 0 else "0")
    ts = f"{sp.bars[0].beats}/{sp.bars[0].beat_type}"

    def ev_to_note(ev: lean_bridge.LeanEvent) -> dict:
        beats = float(ev.ticks) / float(lean_bridge.TICKS_PER_QUARTER)
        dur_name, _ = score_formatter._ticks_to_xml_type(ev.ticks)
        if ev.kind == "R" or not ev.pitches:
            return {"pitch": "REST", "midi": None, "duration": dur_name, "beats": beats, "rest": True, "lyric": ""}
        midi = int(ev.pitches[0])
        step, alter, octv = score_formatter._parse_pitch_parts("", midi)
        acc_sym = "#" if alter > 0 else ("b" if alter < 0 else "")
        tie = "start" if (ev.tie_start and not ev.tie_stop) else ("stop" if (ev.tie_stop and not ev.tie_start) else None)
        out = {"pitch": f"{step}{acc_sym}{octv}", "midi": midi, "duration": dur_name, "beats": beats, "lyric": ""}
        if tie:
            out["tie"] = tie
        return out

    notes = list(map(ev_to_note, chain.from_iterable(map(lambda b: b.events, sp.bars))))
    return {
        "tempo": int(round(score.tempo or 90.0)),
        "time_signature": ts,
        "key": key_name,
        "key_signature": key_sig,
        "notes": notes,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "app": "Psalm Sheet Music Reader & Piano Player"})


@app.route("/api/psalms", methods=["GET"])
def get_psalms_list():
    psalms = psalms_db.list_psalms()
    return jsonify({"psalms": psalms})


@app.route("/api/psalms/<psalm_id>", methods=["GET"])
def get_psalm_detail(psalm_id):
    data = psalms_db.get_psalm(psalm_id)
    if not data:
        return jsonify({"error": "Psalm not found"}), 404
    return jsonify(data)


@app.route("/api/psalms/<psalm_id>/export/<fmt>", methods=["GET"])
def export_psalm(psalm_id, fmt):
    data = psalms_db.get_psalm(psalm_id)
    if not data:
        return jsonify({"error": "Psalm not found"}), 404

    fmt = fmt.lower()
    title_slug = data.get("id", "score")
    speed, augment, voice, count_in, clicks, accompaniment = _parse_export_params()

    if fmt in ["xml", "musicxml"]:
        xml_content = score_formatter.export_musicxml(data, speed=speed, augment=augment)
        return Response(
            xml_content,
            mimetype="application/xml",
            headers={"Content-Disposition": f"attachment; filename={title_slug}.musicxml"},
        )

    if fmt in ["ly", "lilypond"]:
        ly_content = score_formatter.export_lilypond(data, speed=speed, augment=augment)
        return Response(
            ly_content,
            mimetype="text/x-lilypond",
            headers={"Content-Disposition": f"attachment; filename={title_slug}.ly"},
        )

    if fmt in ["mid", "midi"]:
        midi_bytes = score_formatter.export_midi(data, speed=speed, augment=augment)
        return Response(
            midi_bytes,
            mimetype="audio/midi",
            headers={"Content-Disposition": f"attachment; filename={title_slug}.mid"},
        )

    if fmt in ["wav", "audio"]:
        wav_bytes = score_formatter.export_wav_bytes(
            data,
            speed=speed,
            augment=augment,
            voice=voice,
            include_accompaniment=accompaniment,
            include_clicks=clicks,
            count_in_bars=count_in,
        )
        return Response(
            wav_bytes,
            mimetype="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={title_slug}_sing.wav"},
        )

    if fmt == "json":
        return jsonify(data)

    return jsonify({"error": "Unsupported format. Use musicxml, lilypond, midi, wav, or json"}), 400


@app.route("/api/psalms/<psalm_id>/verify", methods=["GET"])
def verify_psalm_lean(psalm_id):
    data = psalms_db.get_psalm(psalm_id)
    if not data:
        return jsonify({"error": "Psalm not found"}), 404

    speed, augment, _, _, _, _ = _parse_export_params()
    s_frac = lean_bridge.Fraction(speed).limit_denominator(1000)
    s_num, s_den = max(1, int(s_frac.numerator)), max(1, int(s_frac.denominator))

    ref_spec = lean_bridge.spec_from_psalm_data(data, speed=1.0, augment=1, pad_incomplete_bars=True)
    xml_text = score_formatter.export_musicxml(data, speed=speed, augment=augment, pad_incomplete_bars=True)
    ly_text = score_formatter.export_lilypond(data, speed=speed, augment=augment, pad_incomplete_bars=True)
    mid_bytes = score_formatter.export_midi(data, speed=speed, augment=augment)

    with tempfile.TemporaryDirectory() as tmp_dir:
        td = Path(tmp_dir)
        xml_p = td / f"{psalm_id}.musicxml"
        ly_p = td / f"{psalm_id}.ly"
        mid_p = td / f"{psalm_id}.mid"
        xml_p.write_text(xml_text, encoding="utf-8")
        ly_p.write_text(ly_text, encoding="utf-8")
        mid_p.write_bytes(mid_bytes)

        parsed_xml = lean_bridge.spec_from_musicxml_file(xml_p)
        parsed_ly = lean_bridge.spec_from_lilypond_file(ly_p)
        mid_notes, mid_tn, mid_td = lean_bridge.sounding_notes_from_midi_file(mid_p)

        report = lean_bridge.verify_bundle_with_lean(
            reference=("original", ref_spec),
            score_entries=(
                ("musicxml", parsed_xml, augment, s_num, s_den),
                ("lilypond", parsed_ly, augment, s_num, s_den),
            ),
            note_entries=(("midi", mid_notes, augment, s_num, s_den, mid_tn, mid_td),),
        )
    return jsonify(report)


@app.route("/api/digitize-all", methods=["POST"])
def batch_digitize():
    try:
        res = digitize_all.digitize_all_psalms()
        return jsonify({"message": "All attached Psalm PDFs digitized cleanly", "count": len(res)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF file uploaded"}), 400
    file = request.files["pdf"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        score_data = pdf_parser.parse_pdf_psalm(tmp_path)
        vec_score = vector_omr.read_score(Path(tmp_path))
        vec_meta = _vector_fallback_notes(vec_score)
        if vec_meta and not score_data.get("matched_preset"):
            score_data["tempo"] = vec_meta["tempo"]
            score_data["time_signature"] = vec_meta["time_signature"]
            score_data["key"] = vec_meta["key"]
            score_data["key_signature"] = vec_meta["key_signature"]
            score_data.setdefault("response", {})["notes"] = vec_meta["notes"]
        psalm_id = psalms_db.save_psalm(score_data)
        score_data["id"] = psalm_id
        return jsonify({"message": "PDF uploaded and digitized successfully", "psalm": score_data})
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route("/karaoke")
def karaoke_page():
    """Serve the interactive Karaoke Note + Word + Background Chord Trainer."""
    return Response(karaoke_trainer.render_standalone_karaoke_html(api_mode=True), mimetype="text/html; charset=utf-8")


@app.route("/api/karaoke/list", methods=["GET"])
def api_karaoke_list():
    """Return available PDF and digitized scores for the Karaoke Trainer."""
    return jsonify({"scores": _list_karaoke_sources()})


@app.route("/api/karaoke/score/<path:score_id>", methods=["GET"])
def api_karaoke_score(score_id):
    """Return aligned melody notes, syllables, phrases, and chords for a Karaoke Trainer score."""
    raw = str(score_id).strip()
    if raw.startswith("pdf:"):
        fname = raw[4:]
        if not fname or Path(fname).name != fname or "/" in fname or "\\" in fname:
            return jsonify({"error": "Invalid PDF name"}), 400
        pdf_path = DATA_DIR / fname
        if not pdf_path.is_file():
            return jsonify({"error": "PDF not found"}), 404
        return jsonify(karaoke_trainer.extract_karaoke_score_from_pdf(pdf_path))
    pid = raw[6:] if raw.startswith("psalm:") else raw
    data = psalms_db.get_psalm(pid)
    if not data:
        return jsonify({"error": "Score not found"}), 404
    return jsonify(karaoke_trainer.extract_karaoke_from_psalm_dict(data))


@app.route("/api/karaoke/upload", methods=["POST"])
def api_karaoke_upload():
    """Extract and return a Karaoke Trainer timeline directly from an uploaded PDF score."""
    file = request.files.get("pdf") or request.files.get("file")
    if file is None:
        return jsonify({"error": "No PDF file uploaded"}), 400
    fname = file.filename or ""
    if not fname.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        data = karaoke_trainer.extract_karaoke_score_from_pdf(Path(tmp_path))
        data["id"] = f"upload:{Path(fname).name}"
        return jsonify(data)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5050)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
    )


# <!-- APAF Bioinformatics | app.py | Approved | 2026-11-15 -->
