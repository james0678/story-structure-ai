"""
Export all Google Docs from a Drive folder as plain text files.

Usage:
    python scripts/export_drive_scripts.py

First run opens a browser for OAuth. token.json is saved for future runs.
"""

import json
import os
import re
from datetime import date
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FOLDER_ID = "1Z7APGs76dDeHwM4k7PBpRlQE9fuu3477"

BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"
OUTPUT_DIR = BASE_DIR / "data" / "scripts"
INDEX_PATH = BASE_DIR / "data" / "projects_index.json"


def authenticate() -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_PATH}\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json())
        print(f"Token saved to {TOKEN_PATH}")

    return creds


def sanitize_filename(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "untitled"


def list_google_docs(service, folder_id: str) -> list[dict]:
    docs = []
    page_token = None

    while True:
        query = (
            f"'{folder_id}' in parents"
            " and mimeType='application/vnd.google-apps.document'"
            " and trashed=false"
        )
        resp = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
                pageSize=100,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
        docs.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return docs


def export_doc_as_text(service, file_id: str) -> str:
    response = (
        service.files()
        .export(fileId=file_id, mimeType="text/plain")
        .execute()
    )
    if isinstance(response, bytes):
        return response.decode("utf-8")
    return response


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Authenticating with Google Drive...")
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)

    print(f"Listing Google Docs in folder {FOLDER_ID}...")
    docs = list_google_docs(service, FOLDER_ID)
    print(f"Found {len(docs)} Google Doc(s)")

    projects = []
    exported = 0
    total_chars = 0

    for doc in docs:
        file_id = doc["id"]
        title = doc["name"]
        project_id = sanitize_filename(title)
        output_path = OUTPUT_DIR / f"{project_id}.txt"

        print(f"  Exporting: {title}")
        try:
            text = export_doc_as_text(service, file_id)
        except HttpError as e:
            print(f"    ERROR exporting {title}: {e}")
            continue

        output_path.write_text(text, encoding="utf-8")
        char_count = len(text)
        total_chars += char_count
        exported += 1

        projects.append(
            {
                "project_id": project_id,
                "title": title,
                "drive_file_id": file_id,
                "export_date": date.today().isoformat(),
                "transcript_path": str(output_path.relative_to(BASE_DIR)),
                "character_count": char_count,
            }
        )
        print(f"    Saved → {output_path.relative_to(BASE_DIR)}  ({char_count:,} chars)")

    index = {"projects": projects}
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nIndex written → {INDEX_PATH.relative_to(BASE_DIR)}")

    print("\n--- Summary ---")
    print(f"Docs found:    {len(docs)}")
    print(f"Docs exported: {exported}")
    print(f"Total chars:   {total_chars:,}")


if __name__ == "__main__":
    main()
