# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Story Structure AI is a FastAPI backend that analyzes interview transcripts using Claude (Anthropic) and the EO Master Storytelling Guide. It returns structured editorial analysis: narrative type, chapter breakdowns, thumbnail suggestions, weak sections, and pitfall warnings. A ChromaDB-backed RAG pipeline provides similar past EO projects as context.

## Commands

```bash
# Activate virtualenv (Python 3.14)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn main:app --reload

# Seed the ChromaDB vector store (required before RAG works)
curl -X POST http://localhost:8000/seed

# Data pipeline (run in order):
python scripts/export_drive_scripts.py   # Export transcripts from Google Drive → data/scripts/
python scripts/build_dataset.py          # Build data/dataset.json from exported scripts
python scripts/download_youtube_transcripts.py  # Download YouTube edited transcripts
python scripts/fetch_youtube_stats.py    # Fetch YouTube video metadata
python scripts/match_scripts.py          # Match originals ↔ YouTube → data/matched_dataset.json
```

## Architecture

**main.py** — FastAPI app with all endpoints:
- `POST /analyze` — Core endpoint. Sends transcript + EO Guide system prompt + RAG context to Claude, returns structured JSON analysis.
- `POST /seed` — Seeds ChromaDB from dataset files.
- `POST /search` — Semantic search over transcripts.
- `GET /projects` / `GET /projects/{id}` — Browse the transcript dataset.

The EO Master Storytelling Guide (~10-part editorial framework) is embedded as a string constant `_GUIDE` in main.py and injected into Claude's system prompt. It defines narrative types (journey vs. situation), chapter design rules, thumbnail formulas, and the 12 common pitfalls.

**rag.py** — ChromaDB vector store module:
- Chunks transcripts (1000 chars, 200 overlap) and stores them with cosine similarity.
- Supports both `matched_dataset.json` (original + edited transcripts) and `dataset.json` (originals only).
- `search_similar()` deduplicates by project_id so results are unique projects.
- `compare_scripts()` uses rapidfuzz to diff original vs. edited transcripts.

**scripts/** — Data pipeline for building the transcript corpus:
- `export_drive_scripts.py` — Google Drive API (requires `credentials.json` + OAuth)
- `build_dataset.py` — Assembles `data/dataset.json` from exported scripts
- `download_youtube_transcripts.py` — Downloads YouTube auto-captions via yt-dlp
- `fetch_youtube_stats.py` — Fetches video metadata from YouTube Data API
- `match_scripts.py` — Fuzzy-matches Drive originals to YouTube transcripts (rapidfuzz, threshold 75)

**data/** — Dataset files (gitignored ChromaDB store at `chroma_db/`):
- `dataset.json` — Original transcripts from Google Drive
- `matched_dataset.json` — Paired original + edited transcripts (preferred by RAG)
- `youtube_metadata.json` — YouTube video stats and edited transcript text

## Environment

Requires `ANTHROPIC_API_KEY` in `.env`. Google Drive scripts require `credentials.json` (OAuth).

## Safety Rules

- NEVER delete or overwrite files in data/ without creating a backup first (copy to data/backups/)
- NEVER modify credentials.json, token.json, or .env
- NEVER push to git remote (local commits only)
- NEVER run rm -rf on any directory
- Always git commit after completing each major section before starting the next
- If a test fails, fix the code — do not skip the test
- If Claude API calls fail (rate limit, auth), retry 3 times with 10s delay before giving up

## What NOT to Touch

- scripts/export_drive_scripts.py — already works, don't refactor
- scripts/download_youtube_transcripts.py — already works, don't refactor
- scripts/fetch_youtube_stats.py — already works, don't refactor
- scripts/build_dataset.py — already works, don't refactor
- The EO Master Storytelling Guide (_GUIDE constant in main.py) — don't modify
- Don't refactor existing working code unless the prompt specifically asks for it
- Don't change the port (always 8000)
