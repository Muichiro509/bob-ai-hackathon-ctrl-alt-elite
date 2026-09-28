# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

- [x] Python 3.10 or higher
- [x] pip (comes with Python)
- [ ] No Node.js, Docker, or cloud account required — runs fully locally

## Environment Variables

Copy `.env.example` to `.env` (optional — the app works with defaults):

```bash
# Windows
copy src\.env.example src\.env

# macOS / Linux
cp src/.env.example src/.env
```

The only variable that matters for local development is `APP_PORT` (default `5000`).
All other variables are unused by the local analysis engine.

| Variable | Description | Required |
|---|---|---|
| `APP_PORT` | Port the Flask server listens on | No (default `5000`) |
| `APP_ENV` | `development` enables `/dry-run`; `production` blocks it | No (default `development`) |
| `WATSONX_API_KEY` | watsonx.ai API key — not used by the local engine | No |

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd bob-ai-hackathon-ctrl-alt-elite

# 2. Install dependencies
pip install -r src/requirements.txt

# (Optional) also install reportlab to regenerate sample PDFs
pip install reportlab
```

## Running the Application

```bash
python src/app.py
```

The application will be available at: **http://localhost:5000**

To use a different port:

```bash
# Windows
set APP_PORT=8000 && python src/app.py

# macOS / Linux
APP_PORT=8000 python src/app.py
```

## Available Routes

| URL | Description |
|---|---|
| `http://localhost:5000/` | Main forensic examination workflow (7-step form) |
| `http://localhost:5000/dry-run` | Developer dry-run console with pipeline trace *(dev only)* |
| `http://localhost:5000/analyze` | POST endpoint used by the UI |

## Running Tests

```bash
python -m pytest src/tests/ -v
```

## Regenerating Sample Data (optional)

```bash
# Regenerate the 8 sample PDFs in demo/sample_documents/
python src/generate_dummy_pdfs.py

# Regenerate the full 50-person database + 200 PDFs in demo/database/
python src/generate_database.py
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r src/requirements.txt` |
| `ModuleNotFoundError: No module named 'reportlab'` | Run `pip install reportlab` (only needed for PDF generation) |
| `Address already in use` on port 5000 | Set `APP_PORT=8000` (or any free port) |
| `/dry-run` returns 403 | Check that `APP_ENV` is not set to `production` |
| `pytest` not found | Run `pip install pytest` |
