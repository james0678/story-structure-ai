"""
Match original Google Drive scripts to YouTube edited transcripts.

Usage:
    python scripts/match_scripts.py

Matching is two-layer:
  1. Manual entries in data/script_mapping.json (always wins)
  2. Fuzzy title match using rapidfuzz (token_sort_ratio >= 75 = high, 60–74 = low)

Outputs:
  data/matched_dataset.json      — matched projects with both transcripts
  data/unmatched_originals.json  — originals with no YouTube match
  data/unmatched_youtube.json    — YouTube videos with no original match
"""

import json
from pathlib import Path

from rapidfuzz import fuzz

BASE_DIR = Path(__file__).parent.parent

DATASET_PATH = BASE_DIR / "data" / "dataset.json"
YOUTUBE_META_PATH = BASE_DIR / "data" / "youtube_metadata.json"
MAPPING_PATH = BASE_DIR / "data" / "script_mapping.json"
MATCHED_PATH = BASE_DIR / "data" / "matched_dataset.json"
UNMATCHED_ORIG_PATH = BASE_DIR / "data" / "unmatched_originals.json"
UNMATCHED_YT_PATH = BASE_DIR / "data" / "unmatched_youtube.json"

FUZZY_HIGH = 75
FUZZY_LOW = 60


def _load_transcript(path_str: str) -> str:
    p = BASE_DIR / path_str
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def main():
    # ── Load sources ──────────────────────────────────────────────────────
    if not DATASET_PATH.exists():
        raise SystemExit(f"{DATASET_PATH} not found. Run build_dataset.py first.")
    if not YOUTUBE_META_PATH.exists():
        raise SystemExit(f"{YOUTUBE_META_PATH} not found. Run download_youtube_transcripts.py first.")

    originals = json.loads(DATASET_PATH.read_text(encoding="utf-8")).get("projects", [])
    yt_data = json.loads(YOUTUBE_META_PATH.read_text(encoding="utf-8"))
    yt_videos = yt_data.get("videos", [])

    manual_mappings: list[dict] = []
    if MAPPING_PATH.exists():
        manual_mappings = json.loads(MAPPING_PATH.read_text(encoding="utf-8")).get("mappings", [])

    # Build lookup dicts
    orig_by_id = {p["project_id"]: p for p in originals}
    yt_by_id = {v["video_id"]: v for v in yt_videos}

    # ── Layer 1: apply manual mappings ────────────────────────────────────
    matched: list[dict] = []
    used_orig_ids: set[str] = set()
    used_yt_ids: set[str] = set()

    for m in manual_mappings:
        oid = m["original_project_id"]
        yid = m["youtube_video_id"]
        if oid not in orig_by_id or yid not in yt_by_id:
            print(f"  WARNING: manual mapping {oid} ↔ {yid} — one side not found, skipping")
            continue
        entry = _build_matched_entry(orig_by_id[oid], yt_by_id[yid], "manual")
        matched.append(entry)
        used_orig_ids.add(oid)
        used_yt_ids.add(yid)

    # ── Layer 2: fuzzy title matching ─────────────────────────────────────
    unmatched_originals = [p for p in originals if p["project_id"] not in used_orig_ids]
    unmatched_yt = [v for v in yt_videos if v["video_id"] not in used_yt_ids]

    fuzzy_candidates: list[tuple[int, dict, dict, str]] = []  # (score, orig, yt_video, confidence)

    for orig in unmatched_originals:
        best_score = 0
        best_yt = None
        orig_title = _clean_title(orig["title"])

        for yt_video in unmatched_yt:
            score = _match_score(orig_title, yt_video["title"])
            if score > best_score:
                best_score = score
                best_yt = yt_video

        if best_yt and best_score >= FUZZY_LOW:
            confidence = "fuzzy-high" if best_score >= FUZZY_HIGH else "fuzzy-low"
            fuzzy_candidates.append((best_score, orig, best_yt, confidence))

    # Sort by score descending, greedily assign best matches
    fuzzy_candidates.sort(key=lambda x: x[0], reverse=True)
    for score, orig, yt_video, confidence in fuzzy_candidates:
        oid = orig["project_id"]
        yid = yt_video["video_id"]
        if oid in used_orig_ids or yid in used_yt_ids:
            continue
        entry = _build_matched_entry(orig, yt_video, confidence)
        matched.append(entry)
        used_orig_ids.add(oid)
        used_yt_ids.add(yid)
        yt_key = _yt_match_key(yt_video["title"])
        print(
            f"  [{score}] {confidence:<11}  "
            f"{_clean_title(orig['title'])[:35]:<35} ↔  {yt_key[:45]}"
        )

    # ── Build unmatched lists ─────────────────────────────────────────────
    final_unmatched_orig = [p for p in originals if p["project_id"] not in used_orig_ids]
    final_unmatched_yt = [v for v in yt_videos if v["video_id"] not in used_yt_ids]

    # ── Save outputs ──────────────────────────────────────────────────────
    MATCHED_PATH.write_text(
        json.dumps({"projects": matched}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    UNMATCHED_ORIG_PATH.write_text(
        json.dumps(
            {"unmatched": [{"project_id": p["project_id"], "title": p["title"]} for p in final_unmatched_orig]},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    UNMATCHED_YT_PATH.write_text(
        json.dumps(
            {"unmatched": [{"video_id": v["video_id"], "title": v["title"]} for v in final_unmatched_yt]},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n{'─'*60}")
    print(f"Original scripts        : {len(originals)}")
    print(f"YouTube videos          : {len(yt_videos)}")
    print(f"Matched (manual)        : {sum(1 for m in matched if m['match_confidence'] == 'manual')}")
    print(f"Matched (fuzzy-high)    : {sum(1 for m in matched if m['match_confidence'] == 'fuzzy-high')}")
    print(f"Matched (fuzzy-low)     : {sum(1 for m in matched if m['match_confidence'] == 'fuzzy-low')}")
    print(f"Total matched           : {len(matched)}")
    print(f"Unmatched originals     : {len(final_unmatched_orig)}")
    print(f"Unmatched YouTube videos: {len(final_unmatched_yt)}")
    print(f"\nSaved → {MATCHED_PATH.relative_to(BASE_DIR)}")
    print(f"       → {UNMATCHED_ORIG_PATH.relative_to(BASE_DIR)}")
    print(f"       → {UNMATCHED_YT_PATH.relative_to(BASE_DIR)}")

    if final_unmatched_orig:
        print("\nUnmatched originals (add to script_mapping.json):")
        for p in final_unmatched_orig:
            print(f"  {p['project_id']}")


def _clean_title(title: str) -> str:
    """Strip common prefixes/suffixes to expose person/company names."""
    import re
    title = re.sub(r"^\[Script\]\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^\[script\]\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^Copy of\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^Script[_\s]+", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^Temporary[_\s]+", "", title, flags=re.IGNORECASE)
    # Remove trailing noise
    title = re.sub(r"\s+(full\s*script|interview|script)$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"[-_]\s*(EP\d+|ep\d+)$", "", title, flags=re.IGNORECASE)
    # Remove parenthetical notes like (2026, 2nd filming)
    title = re.sub(r"\s*[\(\[].*?[\)\]]", "", title)
    # Normalize separators
    title = re.sub(r"[_]+", " ", title)
    return title.strip()


def _yt_match_key(yt_title: str) -> str:
    """
    Extract the most useful part of a YouTube title for matching.
    EO YouTube titles follow the pattern: 'Hook sentence | Company, Person Name'
    The part after | contains person/company and is the best matching key.
    """
    if "|" in yt_title:
        return yt_title.split("|")[-1].strip()
    return yt_title


def _match_score(orig_title: str, yt_title: str) -> int:
    """
    Combined score using both the full YT title and its |suffix.
    Takes the max of token_sort_ratio and a discounted partial_ratio
    (partial_ratio heavily rewards substring matches like 'Legora' in 'Legora, Max...').
    """
    key = _yt_match_key(yt_title)
    score_full = int(fuzz.token_sort_ratio(orig_title, key))
    # partial_ratio rewards short-name matches; discount slightly to avoid false positives
    score_partial = int(fuzz.partial_ratio(orig_title, key) * 0.88)
    return max(score_full, score_partial)


def _build_matched_entry(orig: dict, yt_video: dict, confidence: str) -> dict:
    original_text = orig.get("transcript_original", "") or _load_transcript(
        orig.get("transcript_path", "")
    )
    edited_text = _load_transcript(yt_video.get("transcript_path", ""))

    orig_len = len(original_text)
    edited_len = len(edited_text)
    compression = round(edited_len / orig_len, 4) if orig_len > 0 else None

    return {
        "project_id": orig["project_id"],
        "title": orig["title"],
        "transcript_original": original_text,
        "transcript_edited": edited_text,
        "youtube_video_id": yt_video["video_id"],
        "youtube_title": yt_video["title"],
        "performance": yt_video.get("performance", {}),
        "character_count_original": orig_len,
        "character_count_edited": edited_len,
        "compression_ratio": compression,
        "match_confidence": confidence,
        "metadata": orig.get("metadata", {}),
        "upload_date": yt_video.get("upload_date", ""),
        "duration_seconds": yt_video.get("duration_seconds", 0),
    }


if __name__ == "__main__":
    main()
