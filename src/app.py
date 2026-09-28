import os
import sys
import time

# Ensure src/ is on the path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify, abort
from analyzer import analyze, _classify_and_score, KEYWORD_TRIGGERS, STANDARDS_MAP
from report import generate_report

app = Flask(__name__, template_folder="templates")


# ── Development guard ─────────────────────────────────────────────────────────
def _is_dev():
    """True when APP_ENV is not 'production'."""
    return os.environ.get("APP_ENV", "development").lower() != "production"


# ── Dry-run scenario fixtures ─────────────────────────────────────────────────
DRY_RUN_SCENARIOS = [
    {
        "label":   "Forged COVID Vaccination Certificate",
        "doc_ref": "P001-COV (FC0001 · Conf 0.96)",
        "document_type":  "COVID Vaccination Certificate",
        "examiner_name":  "Dr. Anita Forensics (Dev)",
        "font_obs": (
            "The beneficiary name field uses a different font size and typeface "
            "(Courier) compared to the rest of the certificate (Helvetica). "
            "Visible pixel compression artifacts surround the inserted text block. "
            "Kerning is inconsistent between the heading and the body text. "
            "Character baseline alignment is off by approximately 2px in the "
            "vaccine name field — consistent with copy-paste insertion of text."
        ),
        "signature_obs": (
            "The authorising officer signature is rendered as a flat horizontal "
            "line rather than a natural cursive stroke. No pen lift variations "
            "or tremor consistent with real handwriting. Proportions differ "
            "significantly from reference exemplars on record. Ink density is "
            "uniform throughout — inconsistent with natural writing speed."
        ),
        "paper_obs": (
            "Government seal is misaligned — positioned 4mm above the standard "
            "placement. Under UV light the paper shows fluorescence inconsistent "
            "with standard MoHFW issue stock. Watermark appears faded in the "
            "upper quadrant. Security thread embossing is absent."
        ),
        "ink_obs": (
            "The date field shows evidence of digital alteration — toner adhesion "
            "anomalies in the year segment suggest the digit '0' was substituted "
            "for the letter 'O'. ESDA analysis reveals indented writing beneath "
            "the vaccine name. Multiple ink types detected in a single continuous entry."
        ),
        "metadata_obs": (
            "PDF author field is blank — genuine CoWIN certificates always carry "
            "the MoHFW author string. Creation timestamp is absent. The software "
            "producer tag reads 'Unknown' rather than the CoWIN platform identifier. "
            "No embedded digital signature. Hash value cannot be verified against "
            "the CoWIN portal."
        ),
        "examiner_notes": (
            "Document submitted by Rahul Bhat on 05-Nov-2022. "
            "Cross-verification with CoWIN portal failed — ref no. 9226110045227746 "
            "does not appear in the national registry. Referred to Delhi Cyber Cell."
        ),
    },
    {
        "label":   "Forged Property Sale Deed",
        "doc_ref": "P005-PRO (FC0006 · Conf 0.94)",
        "document_type":  "Property Sale Deed",
        "examiner_name":  "Dr. Anita Forensics (Dev)",
        "font_obs": (
            "Value fields throughout the deed use Courier font while the template "
            "text is in Helvetica — a clear font inconsistency indicating the values "
            "were inserted separately. Character spacing in the area and amount fields "
            "is non-uniform."
        ),
        "signature_obs": (
            "Sub-registrar signature is rendered as a straight horizontal line. "
            "No natural pen lift or cursive stroke variation. Seal impression is "
            "missing from the registrar block — present only as a faded outline."
        ),
        "paper_obs": (
            "Sub-registrar seal is absent from the deed. The stamp paper serial "
            "number embossing is shallow compared to genuine specimens. Paper grain "
            "direction inconsistency detected between pages 1 and 2."
        ),
        "ink_obs": (
            "The e-Challan number contains a zero-for-O substitution (DL23O814OO47). "
            "Toner adhesion anomalies in the numeric fields for area and amount "
            "suggest these were digitally overwritten. Chemical erasure residue "
            "detected under oblique lighting in the consideration amount section."
        ),
        "metadata_obs": (
            "Document number in the header contains letter-O in place of digit-0. "
            "PDF producer metadata is blank. The stated registration date precedes "
            "the deed execution date by 3 days. No digital signature from SRO portal."
        ),
        "examiner_notes": (
            "Referred by South-West Delhi Sub-Registrar. Stated area 269 sq.yd "
            "vs registered 230 sq.yd. Amount discrepancy INR 2,700,000. "
            "Stamp duty paid is inconsistent with the inflated consideration amount."
        ),
    },
    {
        "label":   "Genuine Degree Certificate (no anomalies)",
        "doc_ref": "P002-DEG (genuine · Conf 0.09)",
        "document_type":  "Degree Certificate",
        "examiner_name":  "Dr. Anita Forensics (Dev)",
        "font_obs":       "",
        "signature_obs":  "",
        "paper_obs":      "",
        "ink_obs":        "",
        "metadata_obs":   "",
        "examiner_notes": "Routine employer verification. Physical and digital examination across all five categories found zero anomalies. Document consistent with genuine Mumbai University issue.",
    },
]


@app.route("/")
def home():
    return render_template("index.html")


# ── Dry-run routes (development only) ────────────────────────────────────────

@app.route("/dry-run")
def dry_run():
    """Developer-only dry-run screen. Returns 403 in production."""
    if not _is_dev():
        abort(403)
    return render_template("dry_run.html", scenarios=DRY_RUN_SCENARIOS)


@app.route("/dry-run/execute", methods=["POST"])
def dry_run_execute():
    """Run the full pipeline for a dry-run scenario and return a scoring trace."""
    if not _is_dev():
        abort(403)

    data    = request.get_json(force=True)
    t_start = time.perf_counter()

    observations = {
        "font_inconsistency": data.get("font_obs", ""),
        "signature_mismatch": data.get("signature_obs", ""),
        "paper_anomaly":      data.get("paper_obs", ""),
        "ink_spread":         data.get("ink_obs", ""),
        "digital_metadata":   data.get("metadata_obs", ""),
    }

    # Per-category scoring trace
    scoring_trace = []
    for cat, obs in observations.items():
        if not obs.strip():
            continue
        score, matched = _classify_and_score(obs, cat)
        all_kw = KEYWORD_TRIGGERS.get(cat, [])
        keyword_detail = {kw: (kw in obs.lower()) for kw in all_kw}
        scoring_trace.append({
            "category":        cat,
            "obs_word_count":  len(obs.split()),
            "keywords_total":  len(all_kw),
            "keywords_hit":    len(matched),
            "matched":         matched,
            "keyword_detail":  keyword_detail,
            "raw_score":       score,
            "standard":        STANDARDS_MAP[cat]["standard"],
        })

    result = analyze(
        document_type=data.get("document_type", ""),
        font_obs=data.get("font_obs", ""),
        signature_obs=data.get("signature_obs", ""),
        paper_obs=data.get("paper_obs", ""),
        ink_obs=data.get("ink_obs", ""),
        metadata_obs=data.get("metadata_obs", ""),
        examiner_notes=data.get("examiner_notes", ""),
    )

    report_text = generate_report(
        result, examiner_name=data.get("examiner_name", "Dev Dry-Run")
    )

    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 1)

    findings_json = [
        {
            "category":             f.category,
            "label":                f.label,
            "confidence":           f.confidence,
            "confidence_label":     f.confidence_label,
            "matched_keywords":     f.matched_keywords,
            "standard":             f.standard,
            "standard_description": f.standard_description,
            "relevant_indicators":  f.relevant_indicators,
            "raw_observation":      f.raw_observation,
        }
        for f in result.findings
    ]

    return jsonify({
        "elapsed_ms":       elapsed_ms,
        "scoring_trace":    scoring_trace,
        "observations_sent": {k: bool(v.strip()) for k, v in observations.items()},
        "document_type":              result.document_type,
        "overall_confidence":         result.overall_confidence,
        "overall_confidence_label":   result.overall_confidence_label,
        "verdict":                    result.verdict,
        "anomaly_count":              result.anomaly_count,
        "primary_anomaly":            result.primary_anomaly,
        "findings":                   findings_json,
        "report":                     report_text,
    })


# ── Main analysis route ───────────────────────────────────────────────────────

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
