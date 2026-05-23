"""Download a YouTube video and re-upload it to another YouTube account."""

import sys
from youtube_downloader import download_video, get_video_info
from youtube_uploader import upload_video


def run_pipeline(
    source_url: str,
    privacy_status: str = "private",
    title_prefix: str = "",
) -> str:
    """Download from source URL and upload to authenticated YouTube account."""
    print(f"[1/3] Fetching metadata: {source_url}")
    info = get_video_info(source_url)

    title = f"{title_prefix}{info['title']}" if title_prefix else info["title"]
    description = info.get("description", "")
    tags = info.get("tags", [])

    print(f"  Title    : {title}")
    print(f"  Duration : {info['duration']}s")
    print(f"  Uploader : {info['uploader']}")

    print("\n[2/3] Downloading video...")
    result = download_video(source_url)
    filepath = result["filepath"]
    print(f"  Saved to : {filepath}")

    print(f"\n[3/3] Uploading to YouTube (privacy={privacy_status})...")
    video_id = upload_video(
        filepath=filepath,
        title=title,
        description=description,
        tags=tags,
        privacy_status=privacy_status,
    )

    print(f"\nPipeline complete. Video ID: {video_id}")
    return video_id


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_pipeline.py <youtube_url> [privacy] [title_prefix]")
        print("  privacy: public | unlisted | private (default: private)")
        sys.exit(1)

    url = sys.argv[1]
    privacy = sys.argv[2] if len(sys.argv) > 2 else "private"
    prefix = sys.argv[3] if len(sys.argv) > 3 else ""

    run_pipeline(url, privacy_status=privacy, title_prefix=prefix)
