import os
import sys

# Ensure src/ is on the path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
from analyzer import analyze
from report import generate_report

app = Flask(__name__, template_folder="templates")


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

    return jsonify({
        "document_type": result.document_type,
        "overall_confidence": result.overall_confidence,
        "overall_confidence_label": result.overall_confidence_label,
        "verdict": result.verdict,
        "anomaly_count": result.anomaly_count,
        "primary_anomaly": result.primary_anomaly,
        "findings": findings_json,
        "report": report_text,
    })


if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", 5000))
    app.run(debug=True, port=port)
