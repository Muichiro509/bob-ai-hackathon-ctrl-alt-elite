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

- **3-step guided examination workflow** — Document Info → Observations → Submit & Report
- **Checkbox-based observations screen** — 25 pre-defined forensic findings across 5 collapsible categories; tick findings and assign severity (Minor / Moderate / Strong)
- **Live summary panel** — semicircle confidence gauge, findings count, likely anomaly type, and per-category contribution bars that update instantly as you tick
- **Local rule-based scoring engine** — keyword density + severity modifiers + detail weighting, no ML model or cloud API required
- **Standards mapping** — every finding is automatically linked to ASTM E2285, ASTM E2290, SWGMAT, ISO 32000, or NIST SP 800-86
- **Court-admissible Expert Opinion Report** — structured plain-text report with unique reference ID, per-finding breakdown, and legal disclaimer; copy or print instantly
- **Examination History** — every analysis is saved to `history.json`; slide-in panel lets you re-open any past result with one click
- **Developer dry-run console** at `/dry-run` — 3 preset scenarios (forged COVID cert, forged property deed, genuine degree) with full per-category scoring trace and keyword hit breakdown

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
│   ├── app.py              ← Flask server (7 routes + history helpers + dry-run fixtures)
│   ├── analyzer.py         ← Local forensic analysis engine (scoring, classification, standards)
│   ├── report.py           ← Court-admissible expert opinion report generator
│   ├── requirements.txt    ← Single dependency: flask
│   ├── history.json        ← Auto-created on first analysis run (gitignored)
│   └── templates/
│       ├── index.html      ← 3-step examination UI (checkbox observations + live summary)
│       └── dry_run.html    ← Developer scoring trace console
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

| URL | What it is |
|---|---|
| `http://localhost:5000` | Main app — 3-step examination workflow |
| `http://localhost:5000/dry-run` | Dev console — preset scenarios with scoring trace |

> No `.env` file needed — the engine runs entirely locally with no external services.

---

## 🔍 How It Works

**Observations screen (Step 2)**
The examiner ticks findings from 25 pre-defined indicators across 5 categories and assigns a severity to each. The live summary panel updates the confidence gauge and category bars instantly — before any server call is made.

**Analysis engine** (`src/analyzer.py`) runs in four stages when you submit:

1. **Observation text generation** — ticked findings are converted into natural sentences (`"clear mixed font families..."`, `"significant unnatural tremor suggesting tracing..."`) that the engine can score
2. **Keyword matching** — each sentence is scanned against a bank of ~17 forensic terms per category (`"tremor"`, `"kerning"`, `"erasure"`, `"timestamp"` …)
3. **Scoring** — `score = keyword_density + severity_boost − severity_penalty + detail_bonus` (capped at 1.0); overall = top finding × 40% + mean(rest) × 60%
4. **Verdict + standards mapping** — thresholds: ≥ 70% or 3+ anomalies → *Confirmed Forgery*, ≥ 40% or 2+ → *Suspected Forgery*; each finding is linked to ASTM / SWGMAT / ISO / NIST with up to 4 contextually relevant indicators

**Report generator** (`src/report.py`) then formats a 5-section plain-text court report with a unique reference ID, per-finding confidence bars, standard citations, and a legal disclaimer.

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

- The scoring engine uses keyword matching — the observation sentences generated from checkboxes are designed to trigger the right keywords, but free-text nuance is not captured
- No image upload or OCR; all observations are structured checkbox selections
- History is stored in a local `history.json` file — not suitable for multi-user or networked deployments without modification
- Output is a decision-support tool and must be independently verified by a qualified FDE before use in legal proceedings

---

## 🏅 What We're Most Proud Of

The entirely offline analysis engine — it produces forensically grounded, standards-aligned confidence scores and a fully formatted court-admissible report with zero cloud dependency. The report generator outputs a document with a unique reference ID, timestamped findings, per-category standard citations, and a legal disclaimer — ready to attach to a case file immediately after examination.
