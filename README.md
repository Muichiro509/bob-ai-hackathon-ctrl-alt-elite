# AI-Powered Document Forgery Detection Assistant

> A Bob-powered guided forensic examination workflow for detecting forged documents — built by **Team Ctrl+Alt+Elite**.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Ctrl+Alt+Elite |
| **Track** | AI |
| **Team Lead** | Devang Sorathiya — devangsorathiya502@gmail.com |
| **Members** | Nikunj Patel, Nihar Ladva |

---

## 🎯 Problem Statement

Document forgery is a critical and growing problem across India — fake COVID vaccination certificates were sold in bulk in 2021, the Education Ministry recorded 3,000+ fraudulent degree cases in 2022, and courts regularly receive forged property deeds and altered FIRs. Forensic Document Examiners (FDEs) lack a structured digital tool to systematically record observations across all forensic categories and instantly produce a court-ready expert opinion report.

---

## 💡 Solution

We built a guided forensic examination workflow where an FDE inputs structured observations across five categories — font inconsistencies, signature mismatches, paper anomalies, ink/toner alterations, and digital metadata flags. A local rule-based analysis engine classifies each anomaly, assigns a forgery confidence level (0–100%), maps findings to internationally recognised standards (ASTM, SWGMAT, ISO, NIST), and automatically generates a court-admissible expert opinion report — entirely offline, with no external API dependency.

---

## ✨ Key Features

- **Guided 7-step examination workflow** covering all five forensic observation categories
- **Local rule-based scoring engine** — keyword density + severity modifiers + detail weighting, no ML model or cloud API required
- **Standards mapping** — every finding is automatically linked to ASTM E2285, ASTM E2290, SWGMAT, ISO 32000, or NIST SP 800-86
- **Court-admissible Expert Opinion Report** — structured plain-text report with reference ID, per-finding breakdown, and legal disclaimer, copyable and printable instantly
- **Examination History** — every analysis is saved locally; click any past entry to re-open its full findings and report

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python, HTML, CSS, JavaScript |
| **Frameworks** | Flask |
| **IBM Technologies** | IBM Bob |
| **Databases** | None (file-based history via `history.json`) |
| **Other** | No external API or internet connection required |

---

## 📁 Repository Structure

```
├── src/
│   ├── app.py              ← Flask server — routes: GET /, POST /analyze, GET|DELETE /history
│   ├── analyzer.py         ← Local forensic analysis engine (scoring, classification, standards)
│   ├── report.py           ← Court-admissible expert opinion report generator
│   ├── requirements.txt    ← Single dependency: flask
│   ├── history.json        ← Auto-created on first analysis run (gitignored)
│   └── templates/
│       └── index.html      ← Single-page guided examination UI
├── docs/
│   ├── setup-guide.md
│   ├── architecture.md
│   ├── problem-statement.md
│   └── solution-overview.md
├── demo/
│   ├── screenshots/
│   └── demo-video-link.txt
├── presentation/
└── submission.yaml
```

---

## ⚡ How to Run

No API keys, no database, no Docker — just Python and Flask.

```bash
# 1. Clone the repo
git clone https://github.com/your-org/bob-ai-hackathon-ctrl-alt-elite.git
cd bob-ai-hackathon-ctrl-alt-elite

# 2. Create and activate a virtual environment
cd src
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Open **http://localhost:5000** in your browser.

> No `.env` file needed — the engine runs entirely locally with no external services.

---

## 🔍 How the Analysis Engine Works

The engine in [`src/analyzer.py`](src/analyzer.py) runs in four stages:

1. **Keyword matching** — each observation is scanned against a bank of forensic terms per category (e.g. `"tremor"`, `"tracing"`, `"kerning"`, `"erasure"`, `"timestamp"`)
2. **Scoring** — `score = keyword_density + severity_boost − severity_penalty + detail_bonus` (all capped at 1.0)
3. **Verdict** — overall confidence is a weighted average (top finding × 0.4 + rest × 0.6); verdict thresholds: ≥ 70% or 3+ anomalies → *Confirmed Forgery*, ≥ 40% or 2+ → *Suspected Forgery*
4. **Standards mapping** — each finding is matched to its examination standard and up to 4 contextually relevant indicators are selected for the report

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |

---

## ⚠️ Known Limitations

- The scoring engine uses keyword matching — nuanced observations that avoid standard forensic terminology may receive lower confidence scores than warranted
- No image upload or OCR; all observations must be entered as text by the examiner
- History is stored in a local `history.json` file — not suitable for multi-user or networked deployments without modification
- Output is a decision-support tool and must be independently verified by a qualified FDE before use in legal proceedings

---

## 🏅 What We're Most Proud Of

The entirely offline analysis engine — it produces forensically grounded, standards-aligned confidence scores and a fully formatted court-admissible report with zero cloud dependency. The report generator outputs a document with a unique reference ID, timestamped findings, per-category standard citations, and a legal disclaimer — ready to attach to a case file immediately after examination.
