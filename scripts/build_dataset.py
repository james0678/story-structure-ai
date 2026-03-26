"""
Build data/dataset.json from exported transcripts and projects_index.json.

Usage:
    python scripts/build_dataset.py

Run after export_drive_scripts.py has populated data/scripts/ and
data/projects_index.json.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
INDEX_PATH = BASE_DIR / "data" / "projects_index.json"
DATASET_PATH = BASE_DIR / "data" / "dataset.json"


def main():
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"{INDEX_PATH} not found. Run export_drive_scripts.py first."
        )

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    projects = index.get("projects", [])
    print(f"Building dataset from {len(projects)} project(s)...")

    dataset_projects = []
    for entry in projects:
        transcript_path = BASE_DIR / entry["transcript_path"]
        if not transcript_path.exists():
            print(f"  WARNING: transcript not found for {entry['project_id']}, skipping")
            continue

        text = transcript_path.read_text(encoding="utf-8")
        dataset_projects.append(
            {
                "project_id": entry["project_id"],
                "title": entry["title"],
                "transcript_original": text,
                "character_count": entry["character_count"],
                "metadata": {
                    "drive_file_id": entry["drive_file_id"],
                    "export_date": entry["export_date"],
                },
            }
        )
        print(f"  Added: {entry['title']} ({entry['character_count']:,} chars)")

    dataset = {"projects": dataset_projects}
    DATASET_PATH.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nDataset written → {DATASET_PATH.relative_to(BASE_DIR)}")
    print(f"Total projects: {len(dataset_projects)}")


if __name__ == "__main__":
    main()
