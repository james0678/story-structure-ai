# Story Structure AI

RAG-based tool that analyzes interview transcripts and suggests chapter structures.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Running

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API

### POST /analyze

Analyzes a transcript and returns chapter suggestions.

**Request**
```json
{
  "transcript": "Your interview transcript text here..."
}
```

**Response**
```json
{
  "chapters": [
    { "title": "Introduction", "description": "Guest background" },
    { "title": "Core Insight", "description": "Main idea" },
    { "title": "Deep Dive", "description": "Detailed exploration" }
  ]
}
```
