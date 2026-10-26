import os
import tempfile
from flask import Flask, render_template, jsonify, request, Response
import psalms_db
import score_formatter
import pdf_parser
import digitize_all

app = Flask(__name__, template_folder="templates", static_folder="static")

# Ensure default and digitized scores are loaded
psalms_db.ensure_scores_dir()

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

    if fmt in ["xml", "musicxml"]:
        xml_content = score_formatter.export_musicxml(data)
        return Response(
            xml_content,
            mimetype="application/xml",
            headers={"Content-Disposition": f"attachment; filename={title_slug}.musicxml"}
        )

    elif fmt in ["mid", "midi"]:
        midi_bytes = score_formatter.export_midi(data)
        return Response(
            midi_bytes,
            mimetype="audio/midi",
            headers={"Content-Disposition": f"attachment; filename={title_slug}.mid"}
        )

    elif fmt == "json":
        return jsonify(data)

    return jsonify({"error": "Unsupported format. Use xml, midi, or json"}), 400

@app.route("/api/digitize-all", methods=["POST"])
def digitize_all_endpoint():
    try:
        records = digitize_all.digitize_all_psalms()
        return jsonify({
            "message": f"Successfully digitized {len(records)} Psalm sheet music PDFs",
            "count": len(records)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No pdf file uploaded"}), 400

    file = request.files["pdf"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        score_data = pdf_parser.parse_pdf_psalm(tmp_path)
        psalm_id = psalms_db.save_psalm(score_data)
        score_data["id"] = psalm_id
        return jsonify({
            "message": "PDF uploaded and digitized successfully",
            "psalm": score_data
        })
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    default_port = 5050
    port = int(os.environ.get("PORT", default_port))
    print(f"\n🚀 Starting Psalm Sheet Music Reader at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
