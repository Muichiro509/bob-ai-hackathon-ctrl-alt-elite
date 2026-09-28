# Source Code

This folder contains the complete application source for the **AI-Powered Document Forgery Detection Assistant**.

## Structure

```
src/
├── app.py              ← Flask server
│                         Routes: GET /  · POST /analyze  · GET /history  · DELETE /history[/<id>]
├── analyzer.py         ← Local forensic analysis engine
│                         Keyword scoring, confidence calculation, standards mapping
├── report.py           ← Court-admissible expert opinion report generator
├── requirements.txt    ← Dependencies (flask only)
├── history.json        ← Auto-created on first run; stores all past examinations
├── .env.example        ← Environment variable template (no variables required for this app)
└── templates/
    └── index.html      ← Single-page guided examination UI (7-step form + results + history drawer)
```

## Key Files

### [`app.py`](app.py)
Flask entry point. Handles HTTP routing, calls `analyzer.py` and `report.py`, and persists every analysis result to `history.json`.

| Route | Method | Description |
|---|---|---|
| `/` | GET | Serves the examination UI |
| `/analyze` | POST | Accepts JSON observation payload, returns analysis + report |
| `/history` | GET | Returns all saved examination entries |
| `/history/<id>` | DELETE | Deletes a single history entry |
| `/history` | DELETE | Clears all history |

### [`analyzer.py`](analyzer.py)
The entire analysis engine. No ML model or external API.

- `KEYWORD_TRIGGERS` — 5 category-specific keyword banks (~17 terms each)
- `STANDARDS_MAP` — maps each category to its real forensic standard (ASTM, SWGMAT, ISO, NIST)
- `_classify_and_score()` — keyword density + severity boost/penalty + detail length bonus → score 0–1
- `_verdict()` — thresholds: ≥ 0.70 or 3+ anomalies → Confirmed Forgery; ≥ 0.40 or 2+ → Suspected
- `analyze()` — top-level function; scores all 5 categories and returns a weighted `AnalysisResult`

### [`report.py`](report.py)
Generates a structured plain-text Expert Opinion Report from an `AnalysisResult`. Includes reference ID, timestamps, per-finding breakdown, standard citations, and legal disclaimer.

### [`templates/index.html`](templates/index.html)
Self-contained single-page application. Vanilla HTML/CSS/JS — no build step.
- 7-step guided form (document info → 5 observation categories → submit)
- Results page: verdict banner, confidence meter, collapsible finding cards, full report box (copy/print)
- History drawer: fixed FAB button, slide-in panel, click any entry to re-render its results

## Running Locally

```bash
# From the src/ directory
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

No `.env` file required — this application has no external service dependencies.
