"""
Add retention data to matched_dataset.json and export/import CSV.

Usage:
    python scripts/add_retention_data.py           # Add estimated retention + export CSV
    python scripts/add_retention_data.py --import   # Import real retention data from CSV

Outputs:
    data/retention_data.csv        — CSV for manual editing (fill in avg_view_duration_seconds)
    data/matched_dataset.json      — Updated with retention fields (backup created first)
"""

import csv
import json
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
MATCHED_PATH = BASE_DIR / "data" / "matched_dataset.json"
YOUTUBE_META_PATH = BASE_DIR / "data" / "youtube_metadata.json"
CSV_PATH = BASE_DIR / "data" / "retention_data.csv"
BACKUP_DIR = BASE_DIR / "data" / "backups"


def _backup_matched():
    """Create a backup of matched_dataset.json before modifying."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    import datetime

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"matched_dataset_{ts}.json"
    shutil.copy2(MATCHED_PATH, dest)
    print(f"Backup created: {dest.relative_to(BASE_DIR)}")


def _load_youtube_metadata() -> dict[str, dict]:
    """Load youtube_metadata.json as a dict keyed by video_id."""
    if not YOUTUBE_META_PATH.exists():
        return {}
    data = json.loads(YOUTUBE_META_PATH.read_text(encoding="utf-8"))
    return {v["video_id"]: v for v in data.get("videos", [])}


def _estimate_retention(views: int, likes: int) -> float:
    """Heuristic retention estimate when real data is unavailable."""
    if views <= 0:
        return 0.35
    ratio = 0.35 + (likes / views) * 2
    return round(max(0.2, min(0.7, ratio)), 4)


def add_retention():
    """Add retention fields to matched_dataset.json and export CSV."""
    if not MATCHED_PATH.exists():
        print(f"ERROR: {MATCHED_PATH} not found.")
        return

    _backup_matched()

    data = json.loads(MATCHED_PATH.read_text(encoding="utf-8"))
    yt_meta = _load_youtube_metadata()
    projects = data.get("projects", [])

    csv_rows = []

    for proj in projects:
        perf = proj.get("performance", {})
        views = perf.get("views", 0)
        likes = perf.get("likes", 0)
        comments = perf.get("comments", 0)
        yt_id = proj.get("youtube_video_id", "")
        duration = proj.get("duration_seconds")

        # Try to get duration from youtube_metadata if not in project
        if not duration and yt_id in yt_meta:
            duration = yt_meta[yt_id].get("duration_seconds")
            proj["duration_seconds"] = duration

        # Add retention fields
        proj["avg_view_duration_seconds"] = proj.get("avg_view_duration_seconds")

        if proj["avg_view_duration_seconds"] and duration:
            # Real data available
            proj["retention_ratio"] = round(
                proj["avg_view_duration_seconds"] / duration, 4
            )
            proj["retention_source"] = "manual"
        else:
            # Estimate
            proj["retention_ratio"] = _estimate_retention(views, likes)
            proj["retention_source"] = "estimated"

        # Build YouTube URL
        yt_url = f"https://www.youtube.com/watch?v={yt_id}" if yt_id else ""

        csv_rows.append(
            {
                "project_id": proj["project_id"],
                "youtube_title": proj.get("youtube_title", proj.get("title", "")),
                "youtube_video_id": yt_id,
                "youtube_url": yt_url,
                "video_duration_seconds": duration or "",
                "avg_view_duration_seconds": proj.get("avg_view_duration_seconds") or "",
                "retention_ratio": proj.get("retention_ratio", ""),
                "retention_source": proj.get("retention_source", ""),
                "views": views,
                "likes": likes,
                "comments": comments,
            }
        )

    # Write updated matched_dataset.json
    MATCHED_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Updated {len(projects)} projects in matched_dataset.json")

    # Write CSV
    fieldnames = [
        "project_id",
        "youtube_title",
        "youtube_video_id",
        "youtube_url",
        "video_duration_seconds",
        "avg_view_duration_seconds",
        "retention_ratio",
        "retention_source",
        "views",
        "likes",
        "comments",
    ]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Exported CSV: {CSV_PATH.relative_to(BASE_DIR)}")

    # Print top 10 by retention
    ranked = sorted(projects, key=lambda p: p.get("retention_ratio", 0), reverse=True)
    print("\nTop 10 projects by estimated retention ratio:")
    for i, proj in enumerate(ranked[:10], 1):
        perf = proj.get("performance", {})
        print(
            f"  {i:2d}. {proj['project_id']:<45s} "
            f"retention={proj.get('retention_ratio', 0):.4f} "
            f"({proj.get('retention_source', 'unknown')}) "
            f"views={perf.get('views', 0):>8,} "
            f"likes={perf.get('likes', 0):>5,}"
        )


def import_retention():
    """Import avg_view_duration_seconds from CSV back into matched_dataset.json."""
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Run without --import first.")
        return
    if not MATCHED_PATH.exists():
        print(f"ERROR: {MATCHED_PATH} not found.")
        return

    _backup_matched()

    data = json.loads(MATCHED_PATH.read_text(encoding="utf-8"))
    projects_by_id = {p["project_id"]: p for p in data.get("projects", [])}

    updated = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row["project_id"]
            avg_dur = row.get("avg_view_duration_seconds", "").strip()
            if not avg_dur or pid not in projects_by_id:
                continue

            try:
                avg_dur_val = float(avg_dur)
            except ValueError:
                continue

            proj = projects_by_id[pid]
            proj["avg_view_duration_seconds"] = avg_dur_val
            duration = proj.get("duration_seconds")
            if duration:
                proj["retention_ratio"] = round(avg_dur_val / duration, 4)
            proj["retention_source"] = "manual"
            updated += 1

    MATCHED_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Imported retention data for {updated} projects.")


if __name__ == "__main__":
    if "--import" in sys.argv:
        import_retention()
    else:
        add_retention()
