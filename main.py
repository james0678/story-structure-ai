import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
client = anthropic.Anthropic()

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """\
You are an expert video/podcast editor. Given a transcript, identify logical chapter breaks \
and return a JSON array of chapter suggestions. Each chapter must have:
- "title": a short descriptive title (max 8 words)
- "summary": one sentence describing what this section covers
- "start_excerpt": the first few words of the transcript where this chapter begins

Return ONLY valid JSON — no markdown fences, no extra commentary. Example shape:
[
  {"title": "...", "summary": "...", "start_excerpt": "..."},
  ...
]"""


class AnalyzeRequest(BaseModel):
    transcript: str


class Chapter(BaseModel):
    title: str
    summary: str
    start_excerpt: str


class AnalyzeResponse(BaseModel):
    chapters: list[Chapter]


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(body: AnalyzeRequest):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript must not be empty")

    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Transcript:\n\n{body.transcript}",
            }
        ],
    ) as stream:
        message = stream.get_final_message()

    raw = message.content[0].text.strip()

    import json

    try:
        chapters_data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Model returned invalid JSON: {exc}",
        )

    if not isinstance(chapters_data, list):
        raise HTTPException(
            status_code=502,
            detail="Model response was not a JSON array",
        )

    try:
        chapters = [Chapter(**item) for item in chapters_data]
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Model response shape mismatch: {exc}",
        )

    return AnalyzeResponse(chapters=chapters)
