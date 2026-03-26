"""
Download English subtitles for all non-Short videos on the EO YouTube channel.

Usage:
    python scripts/download_youtube_transcripts.py [CHANNEL_URL]

Default channel: https://www.youtube.com/@EOGlobal/videos
Resume-safe: already-downloaded videos are skipped.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yt_dlp

CHANNEL_URL = "https://www.youtube.com/@EOGlobal/videos"
MIN_DURATION = 120  # skip Shorts

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "edited_scripts"
METADATA_PATH = BASE_DIR / "data" / "youtube_metadata.json"


# ---------------------------------------------------------------------------
# VTT → plain text
# ---------------------------------------------------------------------------

def vtt_to_text(vtt_path: Path) -> str:
    """Strip all VTT markup and return deduplicated clean text."""
    raw = vtt_path.read_text(encoding="utf-8", errors="ignore")

    lines = []
    for line in raw.splitlines():
        line = line.strip()
        # Skip blank lines
        if not line:
            continue
        # Skip WEBVTT header lines
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        # Skip cue index numbers
        if re.match(r"^[\d]+$", line):
            continue
        # Skip any line containing --> (VTT timing cue, with or without alignment annotations)
        if "-->" in line:
            continue
        # Strip inline tags: <00:00:00.000>, <c>, </c>, [music], etc.
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\[[\w\s]+\]", "", line)  # [music], [applause], etc.
        line = line.strip()
        if line:
            lines.append(line)

    # Deduplicate consecutive identical lines (VTT repeats overlapping segments)
    deduped = []
    prev = None
    for line in lines:
        if line != prev:
            deduped.append(line)
        prev = line

    return " ".join(deduped)


# ---------------------------------------------------------------------------
# Pass 1: collect playlist metadata (no download)
# ---------------------------------------------------------------------------

def fetch_playlist_entries(channel_url: str) -> list[dict]:
    opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
    return info.get("entries", [])


# ---------------------------------------------------------------------------
# Pass 2: download subtitles for one video
# ---------------------------------------------------------------------------

def download_subtitles(video_id: str, output_dir: Path) -> Path | None:
    """
    Download best available English subtitles for video_id.
    Returns the path to the saved .vtt file, or None if no subs found.
    """
    opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en", "en-orig"],
        "subtitlesformat": "vtt",
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError:
        return None

    # yt-dlp writes  {id}.en.vtt  or  {id}.en-orig.vtt — prefer manual `en`
    for lang in ("en", "en-orig"):
        candidate = output_dir / f"{video_id}.{lang}.vtt"
        if candidate.exists():
            return candidate
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    channel_url = sys.argv[1] if len(sys.argv) > 1 else CHANNEL_URL
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing metadata so we can resume
    if METADATA_PATH.exists():
        existing = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        videos_by_id = {v["video_id"]: v for v in existing.get("videos", [])}
    else:
        videos_by_id = {}

    print(f"Fetching playlist from {channel_url} ...")
    entries = fetch_playlist_entries(channel_url)
    print(f"Found {len(entries)} entries in playlist")

    # Filter Shorts and entries with no duration info
    long_videos = [e for e in entries if e.get("duration") and e["duration"] >= MIN_DURATION]
    shorts_count = len(entries) - len(long_videos)
    print(f"Skipping {shorts_count} Shorts / no-duration entries → {len(long_videos)} to process\n")

    downloaded = 0
    skipped_existing = 0
    no_captions = []

    for i, entry in enumerate(long_videos, 1):
        video_id = entry["id"]
        title = entry.get("title", "")
        duration = int(entry.get("duration", 0))
        upload_date_raw = entry.get("upload_date", "")  # "20250815"
        description = (entry.get("description") or "")[:500]

        txt_path = OUTPUT_DIR / f"{video_id}.txt"

        # Resume: skip if .txt already produced
        if txt_path.exists():
            skipped_existing += 1
            print(f"[{i}/{len(long_videos)}] SKIP (exists)  {title[:60]}")
            # Ensure metadata entry exists
            if video_id not in videos_by_id:
                videos_by_id[video_id] = {
                    "video_id": video_id,
                    "title": title,
                    "upload_date": _fmt_date(upload_date_raw),
                    "duration_seconds": duration,
                    "description": description,
                    "transcript_path": str(txt_path.relative_to(BASE_DIR)),
                    "character_count": len(txt_path.read_text(encoding="utf-8")),
                }
            continue

        print(f"[{i}/{len(long_videos)}] Downloading  {title[:60]}")
        vtt_path = download_subtitles(video_id, OUTPUT_DIR)

        if vtt_path is None:
            print(f"    ✗ No captions")
            no_captions.append({"video_id": video_id, "title": title})
            continue

        # Convert VTT → plain text
        text = vtt_to_text(vtt_path)
        txt_path.write_text(text, encoding="utf-8")
        # Remove all VTT variants yt-dlp may have written for this video
        for vtt_file in OUTPUT_DIR.glob(f"{video_id}.*.vtt"):
            vtt_file.unlink()

        char_count = len(text)
        downloaded += 1
        print(f"    ✓ {char_count:,} chars")

        videos_by_id[video_id] = {
            "video_id": video_id,
            "title": title,
            "upload_date": _fmt_date(upload_date_raw),
            "duration_seconds": duration,
            "description": description,
            "transcript_path": str(txt_path.relative_to(BASE_DIR)),
            "character_count": char_count,
        }

        # Save incrementally so crashes don't lose progress
        if i % 10 == 0:
            _save_metadata(videos_by_id, no_captions)

    _save_metadata(videos_by_id, no_captions)

    print(f"\n{'─'*50}")
    print(f"Total playlist entries : {len(entries)}")
    print(f"Shorts filtered out    : {shorts_count}")
    print(f"Long videos            : {len(long_videos)}")
    print(f"Already existed        : {skipped_existing}")
    print(f"Downloaded this run    : {downloaded}")
    print(f"No captions / skipped  : {len(no_captions)}")
    print(f"Total in metadata      : {len(videos_by_id)}")
    print(f"Metadata saved to      : {METADATA_PATH.relative_to(BASE_DIR)}")


def _fmt_date(raw: str) -> str:
    """Convert '20250815' → '2025-08-15', or return raw if unparseable."""
    try:
        return datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")
    except Exception:
        return raw


def _save_metadata(videos_by_id: dict, no_captions: list):
    payload = {
        "videos": list(videos_by_id.values()),
        "no_captions": no_captions,
    }
    METADATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
