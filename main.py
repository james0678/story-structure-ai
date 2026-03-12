import json
import os

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """\
You are a senior video editor for EO, a YouTube channel that interviews founders and entrepreneurs. \
You specialize in structuring interview videos for maximum viewer retention.

Given an interview transcript, analyze it and return a JSON object with these fields:
- chapters: array of {title, start_quote, description, estimated_minutes}
- cold_open: {quote, why_it_works} - the most surprising or compelling moment to open the video with
- weak_sections: array of {location, issue, suggestion}
- overall_assessment: one paragraph summary of the interview's strength and how to package it

Return ONLY valid JSON — no markdown fences, no extra commentary."""


class AnalyzeRequest(BaseModel):
    transcript: str


def get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not set. Add it to your .env file.",
        )
    return anthropic.Anthropic(api_key=api_key)


@app.post("/analyze")
def analyze(body: AnalyzeRequest):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript must not be empty")

    client = get_client()

    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Transcript:\n\n{body.transcript}"}],
        ) as stream:
            message = stream.get_final_message()
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=500, detail="Invalid Anthropic API key.")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Anthropic rate limit reached. Try again later.")
    except anthropic.APIStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Anthropic API error {exc.status_code}: {exc.message}")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=502, detail="Could not connect to Anthropic API. Check your network.")

    raw = message.content[0].text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": True, "raw": raw}
