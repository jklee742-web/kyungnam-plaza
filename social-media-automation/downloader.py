"""YouTube 채널에서 영상을 다운로드합니다."""

import os
import json
import yt_dlp
from pathlib import Path
from typing import Optional


def download_channel_videos(
    channel_url: str,
    download_dir: str = "./downloads",
    max_videos: int = 10,
    oldest_first: bool = True,
) -> list[dict]:
    """
    YouTube 채널에서 영상을 다운로드합니다.

    Args:
        channel_url: YouTube 채널 URL 또는 채널 ID
        download_dir: 저장 폴더
        max_videos: 최대 다운로드 영상 수
        oldest_first: True면 오래된순, False면 최신순

    Returns:
        다운로드된 영상 정보 목록
    """
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    metadata_file = os.path.join(download_dir, "downloaded_videos.json")

    # 이미 다운로드된 영상 ID 로드
    downloaded_ids = set()
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            existing = json.load(f)
            downloaded_ids = {v["id"] for v in existing}

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": os.path.join(download_dir, "%(id)s.%(ext)s"),
        "playlistend": max_videos,
        "playlistreverse": oldest_first,
        "ignoreerrors": True,
        "quiet": False,
        "no_warnings": False,
        "writeinfojson": True,
        "writethumbnail": True,
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
    }

    downloaded_videos = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"채널 정보 수집 중: {channel_url}")
        try:
            info = ydl.extract_info(channel_url, download=False)
        except Exception as e:
            print(f"채널 정보 수집 실패: {e}")
            return []

        entries = info.get("entries", [info])
        if oldest_first:
            entries = list(reversed(list(entries)))

        count = 0
        for entry in entries:
            if count >= max_videos:
                break
            if entry is None:
                continue

            video_id = entry.get("id")
            if video_id in downloaded_ids:
                print(f"이미 다운로드됨 (건너뜀): {entry.get('title')}")
                continue

            print(f"\n다운로드 중 [{count+1}/{max_videos}]: {entry.get('title')}")
            try:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                video_path = os.path.join(download_dir, f"{video_id}.mp4")

                video_info = {
                    "id": video_id,
                    "title": entry.get("title", ""),
                    "description": entry.get("description", ""),
                    "tags": entry.get("tags", []),
                    "duration": entry.get("duration", 0),
                    "upload_date": entry.get("upload_date", ""),
                    "thumbnail": entry.get("thumbnail", ""),
                    "local_path": video_path,
                    "uploaded_to": [],
                }
                downloaded_videos.append(video_info)
                downloaded_ids.add(video_id)
                count += 1

            except Exception as e:
                print(f"다운로드 실패 ({entry.get('title')}): {e}")

    # 메타데이터 저장
    all_videos = []
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            all_videos = json.load(f)
    all_videos.extend(downloaded_videos)
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(downloaded_videos)}개 영상 다운로드 완료")
    return downloaded_videos


def load_downloaded_videos(download_dir: str = "./downloads") -> list[dict]:
    """이미 다운로드된 영상 목록을 불러옵니다."""
    metadata_file = os.path.join(download_dir, "downloaded_videos.json")
    if not os.path.exists(metadata_file):
        return []
    with open(metadata_file, "r", encoding="utf-8") as f:
        return json.load(f)


def mark_as_uploaded(
    download_dir: str, video_id: str, platform: str
) -> None:
    """영상이 특정 플랫폼에 업로드됐음을 기록합니다."""
    metadata_file = os.path.join(download_dir, "downloaded_videos.json")
    if not os.path.exists(metadata_file):
        return

    with open(metadata_file, "r", encoding="utf-8") as f:
        videos = json.load(f)

    for video in videos:
        if video["id"] == video_id:
            if platform not in video.get("uploaded_to", []):
                video.setdefault("uploaded_to", []).append(platform)
            break

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
