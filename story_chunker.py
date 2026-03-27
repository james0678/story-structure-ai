"""
Story-level semantic chunker using Claude API.

Segments transcripts into meaningful story beats instead of fixed-size chunks.
Results are cached to data/chunked_scripts/{project_id}_chunks.json.
"""

import hashlib
import json
import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path("data/chunked_scripts")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "claude-haiku-4-5-20251001"
CHARS_PER_MINUTE = 750
MAX_TRANSCRIPT_CHARS = 25_000
OVERLAP_CHARS = 1_000
SECTION_SIZE = 20_000

CHUNKING_PROMPT = """You are segmenting an interview transcript for a video production team.
Break this into meaningful story chunks. Each chunk = ONE coherent topic or story beat.
A chunk about childhood might be 2 minutes. A chunk about a fundraising crisis might be 5 minutes.
Do NOT split mid-story. Keep related content together.

IMPORTANT: Do NOT include the full transcript text in your response. Instead, for each chunk provide:
- chunk_id: sequential integer starting from {start_id}
- topic: one of: childhood, founding moment, fundraising, crisis, growth metrics, product insight, vision, personal sacrifice, industry context, lesson learned, team building, market analysis, competition, pivot, partnership, exit strategy, personal background, technical deep-dive, customer story, failure, success milestone, philosophy, advice, future plans
- summary: one sentence summary of this chunk
- start_phrase: the EXACT first 60-80 characters of this chunk from the transcript (must match exactly)
- end_phrase: the EXACT last 60-80 characters of this chunk from the transcript (must match exactly)
- emotional_tone: one of: inspiring, vulnerable, technical, reflective, intense, humorous, matter-of-fact, passionate, cautious, candid

Return ONLY a valid JSON array. No markdown fences, no extra commentary."""


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    return anthropic.Anthropic(api_key=api_key)


def _transcript_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _cache_path(project_id: str) -> Path:
    return CACHE_DIR / f"{project_id}_chunks.json"


def _load_cache(project_id: str, transcript: str) -> list[dict] | None:
    path = _cache_path(project_id)
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("transcript_hash") == _transcript_hash(transcript):
            return cached["chunks"]
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def _save_cache(project_id: str, transcript: str, chunks: list[dict]) -> None:
    path = _cache_path(project_id)
    data = {
        "project_id": project_id,
        "transcript_hash": _transcript_hash(transcript),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_text_by_markers(
    transcript: str, start_phrase: str, end_phrase: str
) -> str:
    """Extract text between start_phrase and end_phrase from transcript."""
    # Find start
    start_idx = transcript.find(start_phrase)
    if start_idx == -1:
        # Try fuzzy match with first 30 chars
        short = start_phrase[:30]
        start_idx = transcript.find(short)
    if start_idx == -1:
        return ""

    # Find end (search from start_idx)
    end_idx = transcript.find(end_phrase, start_idx)
    if end_idx == -1:
        short = end_phrase[:30]
        end_idx = transcript.find(short, start_idx)
    if end_idx == -1:
        # Fall back to start + 2000 chars
        return transcript[start_idx : start_idx + 2000]

    return transcript[start_idx : end_idx + len(end_phrase)]


def _call_claude_for_chunks(
    client: anthropic.Anthropic,
    transcript_section: str,
    start_id: int = 1,
    retries: int = 3,
) -> list[dict]:
    """Call Claude to identify story chunk boundaries in a transcript section."""
    prompt = CHUNKING_PROMPT.format(start_id=start_id)

    for attempt in range(retries):
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=prompt,
                messages=[{"role": "user", "content": transcript_section}],
            )
            raw = message.content[0].text.strip()

            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0].strip()

            chunk_markers = json.loads(raw)
            if not isinstance(chunk_markers, list):
                raise ValueError("Expected a JSON array")

            # Extract actual text using markers
            chunks = []
            for cm in chunk_markers:
                text = _extract_text_by_markers(
                    transcript_section,
                    cm.get("start_phrase", ""),
                    cm.get("end_phrase", ""),
                )
                chunks.append(
                    {
                        "chunk_id": cm.get("chunk_id", 0),
                        "topic": cm.get("topic", "unknown"),
                        "summary": cm.get("summary", ""),
                        "text": text,
                        "estimated_minutes": round(len(text) / CHARS_PER_MINUTE, 1),
                        "emotional_tone": cm.get("emotional_tone", "matter-of-fact"),
                    }
                )

            return chunks

        except (json.JSONDecodeError, ValueError) as exc:
            if attempt < retries - 1:
                print(
                    f"  Chunk parsing failed (attempt {attempt + 1}): {exc}. Retrying..."
                )
                time.sleep(10)
            else:
                print(f"  Chunk parsing failed after {retries} attempts: {exc}")
                raise

        except (
            anthropic.RateLimitError,
            anthropic.APIStatusError,
            anthropic.APIConnectionError,
        ) as exc:
            if attempt < retries - 1:
                print(f"  API error (attempt {attempt + 1}): {exc}. Retrying in 10s...")
                time.sleep(10)
            else:
                print(f"  API error after {retries} attempts: {exc}")
                raise


def chunk_transcript(
    transcript: str, project_id: str | None = None
) -> list[dict]:
    """
    Segment a transcript into meaningful story chunks using Claude.

    Args:
        transcript: Full interview transcript text.
        project_id: Optional ID for caching. If provided, results are cached.

    Returns:
        List of chunk dicts with keys: chunk_id, topic, summary, text,
        estimated_minutes, emotional_tone.
    """
    if not transcript.strip():
        return []

    # Check cache
    if project_id:
        cached = _load_cache(project_id, transcript)
        if cached is not None:
            print(f"  Loaded {len(cached)} chunks from cache for {project_id}")
            return cached

    client = _get_client()

    if len(transcript) <= MAX_TRANSCRIPT_CHARS:
        chunks = _call_claude_for_chunks(client, transcript, start_id=1)
    else:
        chunks = []
        start = 0
        section_num = 0
        while start < len(transcript):
            end = min(start + SECTION_SIZE, len(transcript))
            section = transcript[start:end]
            section_num += 1
            print(f"  Processing section {section_num} (chars {start}-{end})...")

            start_id = len(chunks) + 1
            section_chunks = _call_claude_for_chunks(
                client, section, start_id=start_id
            )
            chunks.extend(section_chunks)

            # If we've reached the end, stop
            if end >= len(transcript):
                break
            start = end - OVERLAP_CHARS

        # Deduplicate overlapping chunks by summary similarity
        seen_summaries: set[str] = set()
        deduped: list[dict] = []
        for chunk in chunks:
            summary = chunk.get("summary", "")
            if summary not in seen_summaries:
                seen_summaries.add(summary)
                deduped.append(chunk)
        chunks = deduped

        # Renumber
        for i, chunk in enumerate(chunks, 1):
            chunk["chunk_id"] = i

    # Save to cache
    if project_id:
        _save_cache(project_id, transcript, chunks)

    return chunks


if __name__ == "__main__":
    data = json.loads(Path("data/matched_dataset.json").read_text(encoding="utf-8"))
    project = None
    for p in data.get("projects", []):
        if "taletree" in p["project_id"].lower():
            project = p
            break

    if project is None:
        print("TaleTree project not found in matched_dataset.json")
    else:
        print(f"Chunking: {project['title']}")
        print(f"Transcript length: {len(project['transcript_original']):,} chars")
        print()

        chunks = chunk_transcript(
            project["transcript_original"], project_id=project["project_id"]
        )

        print(f"\nTotal chunks: {len(chunks)}")
        print(
            f"Total estimated minutes: {sum(c['estimated_minutes'] for c in chunks):.1f}"
        )
        print()
        for c in chunks:
            print(
                f"  Chunk {c['chunk_id']:2d} | {c['topic']:<25s} | "
                f"{c['estimated_minutes']:5.1f} min | {c['emotional_tone']:<15s} | "
                f"{c['text'][:100]}..."
            )
