"""YouTube Data API v3를 사용해 영상을 업로드합니다."""

import os
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.pickle"
CLIENT_SECRETS_FILE = "youtube_client_secrets.json"


class YouTubeUploader:
    """YouTube Data API v3 업로더"""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """OAuth2 인증을 수행합니다."""
        creds = None

        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # client_secrets.json 파일 생성
                secrets_content = {
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                }
                import json
                with open(CLIENT_SECRETS_FILE, "w") as f:
                    json.dump(secrets_content, f)

                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)

        self.service = build("youtube", "v3", credentials=creds)
        print("YouTube 인증 완료")

    def upload(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list[str] = None,
        category_id: str = "22",
        privacy: str = "public",
    ) -> dict | None:
        """
        YouTube에 영상을 업로드합니다.

        Args:
            video_path: 영상 파일 경로
            title: 영상 제목 (최대 100자)
            description: 설명
            tags: 태그 목록
            category_id: 카테고리 ID (22=People & Blogs)
            privacy: 공개 설정 (public/private/unlisted)

        Returns:
            업로드된 영상 정보 또는 None
        """
        if not os.path.exists(video_path):
            print(f"파일을 찾을 수 없습니다: {video_path}")
            return None

        title = title[:100]  # YouTube 제목 최대 100자

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 10,  # 10MB 청크
        )

        print(f"\nYouTube 업로드 중: {title}")
        try:
            request = self.service.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"  업로드 진행: {progress}%", end="\r")

            video_id = response["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"\nYouTube 업로드 완료: {video_url}")
            return {"id": video_id, "url": video_url}

        except HttpError as e:
            print(f"YouTube 업로드 실패: {e}")
            return None
