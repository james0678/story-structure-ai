from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    transcript: str


@app.post("/analyze")
def analyze(body: AnalyzeRequest):
    return {
        "chapters": [
            {"title": "Introduction", "description": "Guest background"},
            {"title": "Core Insight", "description": "Main idea"},
            {"title": "Deep Dive", "description": "Detailed exploration"},
        ]
    }
