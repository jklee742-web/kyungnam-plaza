"""Meta Graph API를 사용해 Instagram 릴스를 업로드합니다."""

import os
import time
import requests


GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class InstagramUploader:
    """Instagram Graph API 업로더 (비즈니스/크리에이터 계정 필요)"""

    def __init__(
        self,
        access_token: str,
        instagram_account_id: str,
    ):
        self.access_token = access_token
        self.ig_account_id = instagram_account_id

    def _api(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{GRAPH_API_BASE}/{endpoint}"
        params = kwargs.pop("params", {})
        params["access_token"] = self.access_token
        response = requests.request(method, url, params=params, **kwargs)
        response.raise_for_status()
        return response.json()

    def upload(
        self,
        video_path: str,
        caption: str = "",
        share_to_feed: bool = True,
        cover_url: str = None,
    ) -> dict | None:
        """
        Instagram 릴스를 업로드합니다.

        Instagram Graph API는 영상을 직접 업로드하지 않고
        공개 URL에서 가져오는 방식입니다.
        로컬 파일은 먼저 공개 스토리지에 올려야 합니다.

        실제 운영 시에는 video_path 대신 공개 video_url을 사용하세요.

        Args:
            video_path: 영상 파일 경로 (또는 공개 URL)
            caption: 캡션 (해시태그 포함)
            share_to_feed: 피드에도 공유 여부
            cover_url: 커버 이미지 URL

        Returns:
            업로드된 릴스 정보 또는 None
        """
        # 로컬 파일인 경우 경고
        if os.path.exists(video_path):
            print(
                "⚠️  Instagram API는 공개 URL이 필요합니다.\n"
                "   영상을 AWS S3, Google Cloud Storage 등에 먼저 업로드한 후\n"
                "   공개 URL을 사용하세요.\n"
                "   현재 테스트를 위해 video_path를 URL로 처리합니다."
            )
            # 실제 환경에서는 여기서 클라우드 스토리지 업로드 로직 추가
            print("   (실제 운영 시 이 부분에 클라우드 업로드 코드를 추가하세요)")
            return None

        video_url = video_path  # URL인 경우

        print(f"\nInstagram 릴스 업로드 중...")

        try:
            # Step 1: 미디어 컨테이너 생성
            container_params = {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": share_to_feed,
            }
            if cover_url:
                container_params["cover_url"] = cover_url

            container = self._api(
                "POST",
                f"{self.ig_account_id}/media",
                params=container_params,
            )
            container_id = container["id"]
            print(f"  미디어 컨테이너 생성: {container_id}")

            # Step 2: 처리 완료 대기 (최대 5분)
            print("  영상 처리 대기 중...")
            for attempt in range(30):
                time.sleep(10)
                status = self._api(
                    "GET",
                    container_id,
                    params={"fields": "status_code,status"},
                )
                status_code = status.get("status_code")
                print(f"  상태: {status_code} ({attempt+1}/30)")

                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    print(f"  처리 오류: {status.get('status')}")
                    return None

            # Step 3: 게시
            publish = self._api(
                "POST",
                f"{self.ig_account_id}/media_publish",
                params={"creation_id": container_id},
            )
            media_id = publish["id"]
            print(f"Instagram 릴스 업로드 완료. Media ID: {media_id}")
            return {"id": media_id}

        except requests.HTTPError as e:
            print(f"Instagram 업로드 실패: {e.response.text}")
            return None
        except Exception as e:
            print(f"Instagram 업로드 오류: {e}")
            return None
