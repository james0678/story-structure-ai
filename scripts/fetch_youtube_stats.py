"""
Fetch view/like/comment counts for all videos in youtube_metadata.json.

Usage:
    python scripts/fetch_youtube_stats.py

Requires YOUTUBE_API_KEY in .env (simple API key — no OAuth needed for public stats).
Batches up to 50 video IDs per API call.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
METADATA_PATH = BASE_DIR / "data" / "youtube_metadata.json"


def fetch_stats(api_key: str, video_ids: list[str]) -> dict[str, dict]:
    """Return {video_id: {"views": N, "likes": N, "comments": N}} for all IDs."""
    youtube = build("youtube", "v3", developerKey=api_key)
    stats: dict[str, dict] = {}

    # YouTube API allows max 50 IDs per request
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        resp = (
            youtube.videos()
            .list(part="statistics", id=",".join(batch))
            .execute()
        )
        for item in resp.get("items", []):
            s = item.get("statistics", {})
            stats[item["id"]] = {
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
            }

    return stats


def main():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise SystemExit(
            "YOUTUBE_API_KEY not found in .env\n"
            "Add it: YOUTUBE_API_KEY=AIza..."
        )

    if not METADATA_PATH.exists():
        raise SystemExit(f"{METADATA_PATH} not found. Run download_youtube_transcripts.py first.")

    data = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    videos = data.get("videos", [])
    video_ids = [v["video_id"] for v in videos]

    print(f"Fetching stats for {len(video_ids)} videos...")
    stats = fetch_stats(api_key, video_ids)

    updated = 0
    for video in videos:
        vid = video["video_id"]
        if vid in stats:
            video["performance"] = stats[vid]
            updated += 1
        else:
            video.setdefault("performance", {"views": 0, "likes": 0, "comments": 0})

    METADATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Updated {updated}/{len(video_ids)} videos with performance data")
    print(f"Saved → {METADATA_PATH.relative_to(BASE_DIR)}")

    # Show top 5 by views
    with_perf = [v for v in videos if v.get("performance", {}).get("views", 0) > 0]
    top5 = sorted(with_perf, key=lambda v: v["performance"]["views"], reverse=True)[:5]
    if top5:
        print("\nTop 5 by views:")
        for v in top5:
            print(f"  {v['performance']['views']:>10,}  {v['title'][:60]}")


if __name__ == "__main__":
    main()
