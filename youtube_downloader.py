"""YouTube video downloader using yt-dlp."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
VIDEO_FORMAT = os.getenv("VIDEO_FORMAT", "best[ext=mp4]/best")


def download_video(url: str, output_dir: str = DOWNLOAD_DIR) -> dict:
    """Download a YouTube video and return metadata."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": VIDEO_FORMAT,
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "writeinfojson": True,
        "writethumbnail": True,
        "quiet": False,
        "no_warnings": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return {
            "title": info.get("title"),
            "description": info.get("description"),
            "tags": info.get("tags", []),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "upload_date": info.get("upload_date"),
            "filepath": ydl.prepare_filename(info),
        }


def get_video_info(url: str) -> dict:
    """Fetch video metadata without downloading."""
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "description": info.get("description"),
            "tags": info.get("tags", []),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "upload_date": info.get("upload_date"),
            "thumbnail": info.get("thumbnail"),
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_downloader.py <youtube_url>")
        sys.exit(1)

    url = sys.argv[1]
    print(f"Fetching info for: {url}")
    info = get_video_info(url)
    print(f"Title: {info['title']}")
    print(f"Duration: {info['duration']}s")
    print(f"Uploader: {info['uploader']}")

    confirm = input("\nDownload this video? (y/N): ").strip().lower()
    if confirm == "y":
        result = download_video(url)
        print(f"\nDownloaded: {result['filepath']}")
