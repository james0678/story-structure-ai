# Story Structure AI

AI-powered editorial analysis tool for EO Studio. Analyzes interview transcripts using Claude and the EO Master Storytelling Guide, with RAG-powered comparison to past EO videos and their performance data.

Built for EO's content production team to make data-informed editorial decisions about what to keep, cut, or shorten in interview footage.

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────┐
│   React UI  │────▶│  FastAPI Backend (port 8000)                 │
│  (Vite)     │     │                                              │
│  port 5173  │     │  /analyze-v2  ─── story_chunker.py ──┐      │
│             │     │       │            (Claude API)       │      │
│  - Analyze  │     │       ▼                               ▼      │
│  - Projects │     │  rag.py ◀──── ChromaDB ◀──── data/   │      │
│  - Compare  │     │  (search + performance weighting)     │      │
│             │     │       │                               │      │
│             │     │       ▼                               │      │
│             │     │  Claude API ◀── EO Storytelling Guide │      │
│             │     │  (final analysis with KEEP/CUT recs)  │      │
│             │     └──────────────────────────────────────────────┘
└─────────────┘
```

## Setup

```bash
# 1. Python backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# 3. Seed the vector database (requires data/ files)
uvicorn main:app --port 8000 &
curl -X POST http://localhost:8000/seed

# 4. Frontend
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

## Data Pipeline

Run these scripts in order to build the transcript corpus:

```bash
python scripts/export_drive_scripts.py           # Google Drive → data/scripts/
python scripts/build_dataset.py                   # → data/dataset.json
python scripts/download_youtube_transcripts.py    # → data/edited_scripts/
python scripts/fetch_youtube_stats.py             # → data/youtube_metadata.json
python scripts/match_scripts.py                   # → data/matched_dataset.json
python scripts/add_retention_data.py              # → adds retention estimates + data/retention_data.csv
```

To add real retention data from YouTube Studio:
```bash
# 1. Fill in avg_view_duration_seconds column in data/retention_data.csv
# 2. Import it back:
python scripts/add_retention_data.py --import
# 3. Re-seed ChromaDB:
curl -X POST http://localhost:8000/seed
```

## API Endpoints

### POST /analyze-v2 (Full Pipeline)

The main endpoint. Chunks the transcript semantically, finds similar past projects with performance data, and generates editorial recommendations.

```bash
curl -X POST http://localhost:8000/analyze-v2 \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Your interview transcript...",
    "video_length_target": 15,
    "weight_retention": 0.4
  }'
```

Returns: narrative_type, story_chunks with KEEP/CUT/SHORTEN recommendations, chapter_options, warnings, opportunities, killer_quote, cold_open, thumbnail_suggestions.

### POST /compare/{project_id}

Compares original vs edited transcripts at the story-chunk level.

```bash
curl -X POST http://localhost:8000/compare/script-taletree-matt-hagger
```

Returns: chunk-by-chunk survival analysis, topics kept vs cut, compression ratios, patterns.

### POST /analyze (Legacy)

Original single-pass analysis without semantic chunking.

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"transcript": "...", "video_length_target": 20}'
```

### POST /seed

Seeds ChromaDB from dataset files.

```bash
curl -X POST http://localhost:8000/seed
```

### POST /search

Semantic search over transcripts with performance weighting.

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"transcript": "fundraising story", "n_results": 5}'
```

### GET /projects

List all projects with basic metadata.

```bash
curl http://localhost:8000/projects
```

### GET /projects/{project_id}

Full project detail including transcripts and performance data.

```bash
curl http://localhost:8000/projects/script-taletree-matt-hagger
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Pages:
- **/** — Paste transcript, set target length, analyze
- **/analysis** — Results with color-coded KEEP/CUT/SHORTEN chunks, chapter options, warnings
- **/projects** — Browse all projects, view details, trigger comparisons
- **/compare/{id}** — Side-by-side original vs edited chunk analysis
