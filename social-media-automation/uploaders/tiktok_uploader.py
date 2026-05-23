"""TikTok Content Posting API를 사용해 영상을 업로드합니다."""

import os
import time
import requests


TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"


class TikTokUploader:
    """TikTok Content Posting API 업로더"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def _get_creator_info(self) -> dict:
        """업로드 가능한 설정값을 조회합니다."""
        response = requests.post(
            f"{TIKTOK_API_BASE}/post/publish/creator_info/query/",
            headers=self.headers,
            json={},
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def upload(
        self,
        video_path: str,
        title: str = "",
        privacy: str = "PUBLIC_TO_EVERYONE",
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False,
    ) -> dict | None:
        """
        TikTok에 영상을 업로드합니다.

        Args:
            video_path: 영상 파일 경로
            title: 영상 제목/설명 (최대 2200자)
            privacy: 공개 설정
                - PUBLIC_TO_EVERYONE
                - MUTUAL_FOLLOW_FRIENDS
                - FOLLOWER_OF_CREATOR
                - SELF_ONLY
            disable_comment: 댓글 비활성화
            disable_duet: 듀엣 비활성화
            disable_stitch: 스티치 비활성화

        Returns:
            업로드 결과 또는 None
        """
        if not os.path.exists(video_path):
            print(f"파일을 찾을 수 없습니다: {video_path}")
            return None

        file_size = os.path.getsize(video_path)
        print(f"\nTikTok 업로드 중: {os.path.basename(video_path)}")

        try:
            # Step 1: 업로드 초기화
            init_payload = {
                "post_info": {
                    "title": title[:2200],
                    "privacy_level": privacy,
                    "disable_comment": disable_comment,
                    "disable_duet": disable_duet,
                    "disable_stitch": disable_stitch,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": file_size,
                    "total_chunk_count": 1,
                },
            }

            init_response = requests.post(
                f"{TIKTOK_API_BASE}/post/publish/video/init/",
                headers=self.headers,
                json=init_payload,
            )
            init_response.raise_for_status()
            init_data = init_response.json().get("data", {})

            publish_id = init_data.get("publish_id")
            upload_url = init_data.get("upload_url")

            if not upload_url:
                print(f"TikTok 업로드 초기화 실패: {init_response.text}")
                return None

            print(f"  업로드 ID: {publish_id}")

            # Step 2: 영상 업로드 (단일 청크)
            with open(video_path, "rb") as f:
                video_data = f.read()

            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
                "Content-Length": str(file_size),
            }

            upload_response = requests.put(
                upload_url,
                headers=upload_headers,
                data=video_data,
            )

            if upload_response.status_code not in (200, 201, 206):
                print(f"TikTok 영상 업로드 실패: {upload_response.status_code}")
                return None

            print("  영상 파일 전송 완료")

            # Step 3: 처리 상태 확인 (최대 5분)
            print("  TikTok 처리 대기 중...")
            for attempt in range(30):
                time.sleep(10)
                status_response = requests.post(
                    f"{TIKTOK_API_BASE}/post/publish/status/fetch/",
                    headers=self.headers,
                    json={"publish_id": publish_id},
                )
                status_data = status_response.json().get("data", {})
                status = status_data.get("status")
                print(f"  상태: {status} ({attempt+1}/30)")

                if status == "PUBLISH_COMPLETE":
                    print(f"TikTok 업로드 완료. Publish ID: {publish_id}")
                    return {"publish_id": publish_id}
                elif status in ("FAILED", "PROCESSING_FAILED"):
                    fail_reason = status_data.get("fail_reason", "알 수 없는 오류")
                    print(f"TikTok 처리 실패: {fail_reason}")
                    return None

            print("TikTok 업로드 타임아웃")
            return None

        except requests.HTTPError as e:
            print(f"TikTok API 오류: {e.response.text}")
            return None
        except Exception as e:
            print(f"TikTok 업로드 오류: {e}")
            return None
