"""YouTube video uploader using Google API v3."""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

load_dotenv()

CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
TOKEN_FILE = os.getenv("YOUTUBE_TOKEN_FILE", "token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

RETRIABLE_STATUS_CODES = {500, 502, 503, 504}
MAX_RETRIES = 10


def get_authenticated_service():
    """Authenticate and return a YouTube API service object."""
    creds = None

    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CLIENT_SECRETS_FILE).exists():
                raise FileNotFoundError(
                    f"OAuth credentials file not found: {CLIENT_SECRETS_FILE}\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(
    filepath: str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "22",  # 22 = People & Blogs
    privacy_status: str = "private",
) -> str:
    """Upload a video to YouTube and return the video ID."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Video file not found: {filepath}")

    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }

    media = MediaFileUpload(filepath, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    video_id = _resumable_upload(request)
    return video_id


def _resumable_upload(request) -> str:
    """Execute a resumable upload with exponential backoff retry."""
    response = None
    error = None
    retry = 0

    while response is None:
        try:
            print("Uploading...")
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"  Progress: {pct}%")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP {e.resp.status}: {e.content}"
            else:
                raise
        except Exception as e:
            error = str(e)

        if error:
            retry += 1
            if retry > MAX_RETRIES:
                raise RuntimeError(f"Upload failed after {MAX_RETRIES} retries: {error}")
            wait = 2 ** retry
            print(f"  Retrying in {wait}s... (attempt {retry}/{MAX_RETRIES})")
            time.sleep(wait)
            error = None

    video_id = response["id"]
    print(f"Upload complete. Video ID: {video_id}")
    print(f"URL: https://www.youtube.com/watch?v={video_id}")
    return video_id


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python youtube_uploader.py <video_file> <title> [description] [privacy]")
        print("  privacy: public | unlisted | private (default: private)")
        sys.exit(1)

    filepath = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3] if len(sys.argv) > 3 else ""
    privacy = sys.argv[4] if len(sys.argv) > 4 else "private"

    video_id = upload_video(filepath, title, description, privacy_status=privacy)
    print(f"\nDone! Video ID: {video_id}")
