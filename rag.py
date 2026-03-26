"""
RAG module — ChromaDB-backed semantic search over EO interview transcripts.

Supports two data sources:
  - data/matched_dataset.json  (preferred — has both original + edited transcripts)
  - data/dataset.json          (fallback — originals only)
"""

import json
from pathlib import Path

import chromadb

COLLECTION_NAME = "transcripts"
DB_PATH = "./chroma_db"
MATCHED_DATASET_PATH = "data/matched_dataset.json"
DATASET_PATH = "data/dataset.json"


def init_db() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=DB_PATH)


def _get_collection(client: chromadb.PersistentClient):
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += chunk_size - overlap
    return chunks


def _resolve_dataset_path() -> tuple[str, bool]:
    """Return (path, is_matched). Prefers matched_dataset.json."""
    if Path(MATCHED_DATASET_PATH).exists():
        return MATCHED_DATASET_PATH, True
    return DATASET_PATH, False


def seed_from_dataset(dataset_path: str | None = None) -> dict:
    """
    Chunk and embed all transcripts into ChromaDB.

    When matched_dataset.json is available:
      - Stores BOTH original and edited chunks
      - Each chunk has metadata: project_id, title, chunk_index, source ("original"|"edited")

    Falls back to dataset.json (originals only, source="original").
    Returns {"projects": N, "chunks": M, "source": "matched"|"original_only"}.
    """
    if dataset_path is None:
        dataset_path, is_matched = _resolve_dataset_path()
    else:
        is_matched = "matched" in dataset_path

    client = init_db()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = _get_collection(client)

    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    projects = data.get("projects", [])

    total_chunks = 0
    for project in projects:
        pid = project["project_id"]
        title = project["title"]

        def _add(text: str, source: str):
            nonlocal total_chunks
            if not text.strip():
                return
            chunks = _chunk_text(text)
            prefix = f"{pid}__{source}"
            collection.add(
                ids=[f"{prefix}__chunk_{i}" for i in range(len(chunks))],
                documents=chunks,
                metadatas=[
                    {"project_id": pid, "title": title, "chunk_index": i, "source": source}
                    for i in range(len(chunks))
                ],
            )
            total_chunks += len(chunks)

        _add(project.get("transcript_original", ""), "original")
        if is_matched:
            _add(project.get("transcript_edited", ""), "edited")

    source_label = "matched" if is_matched else "original_only"
    return {"projects": len(projects), "chunks": total_chunks, "source": source_label}


def _load_performance_data() -> dict[str, dict]:
    """Load performance + retention data from matched_dataset.json, keyed by project_id."""
    path = Path(MATCHED_DATASET_PATH)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for p in data.get("projects", []):
        pid = p["project_id"]
        perf = p.get("performance", {})
        result[pid] = {
            "views": perf.get("views", 0),
            "likes": perf.get("likes", 0),
            "comments": perf.get("comments", 0),
            "retention_ratio": p.get("retention_ratio"),
            "retention_source": p.get("retention_source"),
            "duration_seconds": p.get("duration_seconds"),
            "transcript_edited": p.get("transcript_edited", ""),
        }
    return result


def _check_survived_editing(chunk_text: str, edited_transcript: str) -> bool:
    """Check if chunk content survived into the edited transcript."""
    if not edited_transcript or not chunk_text:
        return False
    try:
        from rapidfuzz import fuzz
        # Use first 300 chars of chunk for comparison
        sample = chunk_text[:300]
        score = fuzz.partial_ratio(sample, edited_transcript)
        return score >= 55
    except ImportError:
        return False


def search_similar(
    query: str,
    n_results: int = 3,
    source: str | None = None,
    weight_retention: float = 0.4,
) -> list[dict]:
    """
    Return up to n_results unique projects whose chunks best match the query.

    Results are weighted by both semantic similarity and retention performance.

    Args:
        query: text to search for
        n_results: max unique projects to return
        source: filter to "original", "edited", or None (both)
        weight_retention: weight for retention in combined score (0-1)

    Each result includes similarity_score, retention_ratio, combined_score,
    views, and survived_editing.
    """
    client = init_db()
    collection = _get_collection(client)

    total = collection.count()
    if total == 0:
        return []

    perf_data = _load_performance_data()

    fetch = min(n_results * 10, total)
    query_kwargs: dict = {"query_texts": [query], "n_results": fetch}
    if source:
        query_kwargs["where"] = {"source": source}

    raw = collection.query(**query_kwargs)

    seen: set[str] = set()
    candidates: list[dict] = []

    for doc, meta, dist in zip(
        raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
    ):
        pid = meta["project_id"]
        if pid in seen:
            continue
        seen.add(pid)

        similarity = round(1 - dist, 4)
        proj_perf = perf_data.get(pid, {})
        retention = proj_perf.get("retention_ratio")
        views = proj_perf.get("views", 0)
        edited_transcript = proj_perf.get("transcript_edited", "")

        # Compute combined score
        if retention is not None:
            combined = round(
                similarity * (1 - weight_retention) + retention * weight_retention, 4
            )
        else:
            combined = similarity

        survived = _check_survived_editing(doc, edited_transcript)

        candidates.append(
            {
                "project_id": pid,
                "title": meta["title"],
                "chunk_index": meta["chunk_index"],
                "source": meta.get("source", "original"),
                "matching_chunk": doc,
                "similarity_score": similarity,
                "retention_ratio": retention,
                "combined_score": combined,
                "views": views,
                "survived_editing": survived,
            }
        )

    # Sort by combined_score descending
    candidates.sort(key=lambda x: x["combined_score"], reverse=True)
    return candidates[:n_results]


def get_project(project_id: str, dataset_path: str | None = None) -> dict | None:
    """Return the full project entry, or None if not found."""
    if dataset_path is None:
        dataset_path, _ = _resolve_dataset_path()
    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    for p in data.get("projects", []):
        if p["project_id"] == project_id:
            return p
    return None


def compare_scripts(project_id: str) -> dict | None:
    """
    Return a basic comparison between original and edited transcripts.

    Returns:
        {
          "project_id": ...,
          "title": ...,
          "compression_ratio": 0.24,
          "original_chars": N,
          "edited_chars": N,
          "shared_sections": [...],    # original paragraphs found in edited
          "original_only_sections": [...],  # original paragraphs NOT in edited
        }
    Returns None if project not found or edited transcript is missing.
    """
    try:
        from rapidfuzz import fuzz as _fuzz
    except ImportError:
        return {"error": "rapidfuzz not installed. Run: pip install rapidfuzz"}

    project = get_project(project_id)
    if project is None:
        return None

    original = project.get("transcript_original", "")
    edited = project.get("transcript_edited", "")

    if not original or not edited:
        return {
            "project_id": project_id,
            "title": project.get("title", ""),
            "error": "missing original or edited transcript",
        }

    orig_len = len(original)
    edit_len = len(edited)

    # Strip timestamps/noise before text comparison
    original_clean = _strip_transcript_noise(original)
    edited_clean = _strip_transcript_noise(edited)

    # Split cleaned original into ~500-char paragraphs
    paragraphs = _split_paragraphs(original_clean, target_size=500)

    shared = []
    original_only = []
    for para in paragraphs:
        score = _fuzz.partial_ratio(para[:300], edited_clean)
        if score >= 60:
            shared.append(para[:200])
        else:
            original_only.append(para[:200])

    return {
        "project_id": project_id,
        "title": project.get("title", ""),
        "compression_ratio": round(edit_len / orig_len, 4) if orig_len else None,
        "original_chars": orig_len,
        "edited_chars": edit_len,
        "paragraphs_analyzed": len(paragraphs),
        "shared_sections_count": len(shared),
        "original_only_sections_count": len(original_only),
        "shared_sections": shared[:5],
        "original_only_sections": original_only[:5],
    }


def _strip_transcript_noise(text: str) -> str:
    """Remove timestamps, speaker labels, and formatting noise before text comparison."""
    import re
    text = re.sub(r"\[\d{2}:\d{2}(:\d{2})?\]", " ", text)   # [00:00:00] or [00:00]
    text = re.sub(r"Speaker\s*\d*\s*:", " ", text)             # Speaker: / Speaker 2:
    text = re.sub(r"^===+$", "", text, flags=re.MULTILINE)     # === dividers
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_paragraphs(text: str, target_size: int = 500) -> list[str]:
    """Split text into chunks at sentence boundaries near target_size."""
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text)
    paragraphs = []
    current = []
    current_len = 0
    for sent in sentences:
        current.append(sent)
        current_len += len(sent)
        if current_len >= target_size:
            paragraphs.append(" ".join(current))
            current = []
            current_len = 0
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs
