#!/usr/bin/env python3
"""
소셜 미디어 자동 업로드 시스템
YouTube 채널에서 영상을 다운로드하여 YouTube, Instagram, TikTok에 자동 업로드합니다.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

from downloader import download_channel_videos, load_downloaded_videos, mark_as_uploaded
from uploaders import YouTubeUploader, InstagramUploader, TikTokUploader

load_dotenv()


def get_env(key: str, required: bool = True) -> str | None:
    value = os.getenv(key)
    if required and not value:
        print(f"오류: .env 파일에 {key}가 설정되지 않았습니다.")
        sys.exit(1)
    return value


def run_download(args):
    """YouTube 채널에서 영상을 다운로드합니다."""
    channel_url = args.channel_url or get_env("SOURCE_CHANNEL_URL")
    max_videos = args.max_videos or int(os.getenv("MAX_VIDEOS", "10"))
    download_dir = args.download_dir or os.getenv("DOWNLOAD_DIR", "./downloads")

    print(f"채널: {channel_url}")
    print(f"최대 {max_videos}개 영상 (오래된순)")
    print("-" * 50)

    videos = download_channel_videos(
        channel_url=channel_url,
        download_dir=download_dir,
        max_videos=max_videos,
        oldest_first=True,
    )

    print(f"\n다운로드 완료: {len(videos)}개 영상")
    for v in videos:
        print(f"  - {v['title']} ({v['id']})")


def run_upload(args):
    """다운로드된 영상을 소셜 미디어에 업로드합니다."""
    download_dir = args.download_dir or os.getenv("DOWNLOAD_DIR", "./downloads")
    platforms = args.platforms or ["youtube", "instagram", "tiktok"]

    videos = load_downloaded_videos(download_dir)
    if not videos:
        print("업로드할 영상이 없습니다. 먼저 'download' 명령을 실행하세요.")
        return

    # 업로더 초기화
    uploaders = {}

    if "youtube" in platforms:
        try:
            uploaders["youtube"] = YouTubeUploader(
                client_id=get_env("YOUTUBE_CLIENT_ID"),
                client_secret=get_env("YOUTUBE_CLIENT_SECRET"),
            )
        except SystemExit:
            print("YouTube 인증 정보가 없습니다. .env 파일을 확인하세요.")

    if "instagram" in platforms:
        ig_token = os.getenv("META_ACCESS_TOKEN")
        ig_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        if ig_token and ig_account_id:
            uploaders["instagram"] = InstagramUploader(
                access_token=ig_token,
                instagram_account_id=ig_account_id,
            )
        else:
            print("Instagram 인증 정보가 없습니다. (META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID)")

    if "tiktok" in platforms:
        tt_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        if tt_token:
            uploaders["tiktok"] = TikTokUploader(access_token=tt_token)
        else:
            print("TikTok 인증 정보가 없습니다. (TIKTOK_ACCESS_TOKEN)")

    if not uploaders:
        print("활성화된 업로더가 없습니다.")
        return

    # 영상 업로드
    for video in videos:
        video_id = video["id"]
        already_uploaded = video.get("uploaded_to", [])

        print(f"\n{'='*50}")
        print(f"영상: {video['title']}")
        print(f"파일: {video.get('local_path', '없음')}")

        local_path = video.get("local_path", "")
        if not os.path.exists(local_path):
            print(f"  파일 없음, 건너뜀: {local_path}")
            continue

        for platform, uploader in uploaders.items():
            if platform in already_uploaded and not args.force:
                print(f"  [{platform}] 이미 업로드됨 (--force로 재업로드 가능)")
                continue

            print(f"\n  [{platform}] 업로드 시작...")

            if platform == "youtube":
                result = uploader.upload(
                    video_path=local_path,
                    title=video.get("title", "제목 없음"),
                    description=video.get("description", ""),
                    tags=video.get("tags", []),
                    privacy="public",
                )
            elif platform == "instagram":
                result = uploader.upload(
                    video_path=local_path,
                    caption=f"{video.get('title', '')}\n\n{video.get('description', '')[:200]}",
                )
            elif platform == "tiktok":
                result = uploader.upload(
                    video_path=local_path,
                    title=video.get("title", "")[:150],
                    privacy="PUBLIC_TO_EVERYONE",
                )

            if result:
                mark_as_uploaded(download_dir, video_id, platform)
                print(f"  [{platform}] 완료!")
            else:
                print(f"  [{platform}] 업로드 실패")


def run_all(args):
    """다운로드 후 모든 플랫폼에 업로드합니다."""
    run_download(args)
    run_upload(args)


def main():
    parser = argparse.ArgumentParser(
        description="소셜 미디어 자동 업로드 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py download                              # 채널에서 영상 다운로드
  python main.py upload                               # 모든 플랫폼에 업로드
  python main.py upload --platforms youtube tiktok    # 특정 플랫폼만 업로드
  python main.py all                                  # 다운로드 후 전체 업로드
  python main.py all --max-videos 5                   # 최근 5개만 처리
        """,
    )

    parser.add_argument("--download-dir", default=None, help="영상 저장 폴더")
    parser.add_argument("--channel-url", default=None, help="YouTube 채널 URL")
    parser.add_argument("--max-videos", type=int, default=None, help="최대 영상 수")
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["youtube", "instagram", "tiktok"],
        default=None,
        help="업로드할 플랫폼",
    )
    parser.add_argument("--force", action="store_true", help="이미 업로드된 영상도 재업로드")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("download", help="YouTube에서 영상 다운로드")
    subparsers.add_parser("upload", help="소셜 미디어에 업로드")
    subparsers.add_parser("all", help="다운로드 후 전체 업로드")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "download": run_download,
        "upload": run_upload,
        "all": run_all,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
