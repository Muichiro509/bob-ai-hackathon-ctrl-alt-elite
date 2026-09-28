import os
import sys
import json
from datetime import datetime

# Ensure src/ is on the path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
from analyzer import analyze
from report import generate_report

app = Flask(__name__, template_folder="templates")

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")


def _load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def run_analysis():
    data = request.get_json(force=True)

    result = analyze(
        document_type=data.get("document_type", ""),
        font_obs=data.get("font_obs", ""),
        signature_obs=data.get("signature_obs", ""),
        paper_obs=data.get("paper_obs", ""),
        ink_obs=data.get("ink_obs", ""),
        metadata_obs=data.get("metadata_obs", ""),
        examiner_notes=data.get("examiner_notes", ""),
    )

    report_text = generate_report(result, examiner_name=data.get("examiner_name", "Forensic Document Examiner"))

    # Serialise findings for JSON
    findings_json = [
        {
            "category": f.category,
            "label": f.label,
            "confidence": f.confidence,
            "confidence_label": f.confidence_label,
            "matched_keywords": f.matched_keywords,
            "standard": f.standard,
            "standard_description": f.standard_description,
            "relevant_indicators": f.relevant_indicators,
            "raw_observation": f.raw_observation,
        }
        for f in result.findings
    ]

    response = {
        "document_type": result.document_type,
        "overall_confidence": result.overall_confidence,
        "overall_confidence_label": result.overall_confidence_label,
        "verdict": result.verdict,
        "anomaly_count": result.anomaly_count,
        "primary_anomaly": result.primary_anomaly,
        "findings": findings_json,
        "report": report_text,
    }

    # Persist to history
    history = _load_history()
    entry = {
        "id": datetime.now().strftime("FDE-%Y%m%d-%H%M%S"),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "examiner_name": data.get("examiner_name", ""),
        **response,
    }
    history.insert(0, entry)   # newest first
    _save_history(history)

    return jsonify(response)


@app.route("/history", methods=["GET"])
def get_history():
    return jsonify(_load_history())


@app.route("/history/<entry_id>", methods=["DELETE"])
def delete_history_entry(entry_id):
    history = _load_history()
    history = [e for e in history if e["id"] != entry_id]
    _save_history(history)
    return jsonify({"ok": True})


@app.route("/history", methods=["DELETE"])
def clear_history():
    _save_history([])
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", 5000))
    app.run(debug=True, port=port)
