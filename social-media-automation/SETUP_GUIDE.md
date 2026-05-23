# 소셜 미디어 자동 업로드 시스템 - 설정 가이드

## 설치

```bash
cd social-media-automation
pip install -r requirements.txt
cp .env.example .env
# .env 파일을 열어 API 키 입력
```

---

## 플랫폼별 API 설정

### 1. YouTube (Google Cloud Console)

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성
3. **API 및 서비스 > 라이브러리** → "YouTube Data API v3" 활성화
4. **API 및 서비스 > 사용자 인증 정보** → "OAuth 2.0 클라이언트 ID" 생성
   - 애플리케이션 유형: **데스크톱 앱**
5. 클라이언트 ID와 시크릿을 `.env`에 입력

```env
YOUTUBE_CLIENT_ID=123456789-xxx.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-xxxxxxxxxx
```

> 첫 실행 시 브라우저에서 Google 계정 로그인 화면이 뜹니다. 인증 후 자동으로 토큰이 저장됩니다.

---

### 2. Instagram (Meta for Developers)

**⚠️ 비즈니스 또는 크리에이터 계정 필요**

1. [Meta for Developers](https://developers.facebook.com/) 접속
2. 앱 생성 → **비즈니스** 유형 선택
3. **Instagram Graph API** 제품 추가
4. Instagram 계정을 Facebook 페이지에 연결
5. **Graph API Explorer**에서 장기 액세스 토큰 발급
   - 필요 권한: `instagram_content_publish`, `instagram_basic`
6. Instagram 비즈니스 계정 ID 확인

```env
META_APP_ID=1234567890
META_APP_SECRET=abcdefg1234567
META_ACCESS_TOKEN=EAAxxxxxxxxx (장기 토큰, 60일 유효)
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000
```

> **중요**: Instagram API는 영상 공개 URL이 필요합니다. 로컬 파일을 먼저 AWS S3, Cloudflare R2 등에 업로드해야 합니다.

---

### 3. TikTok (TikTok for Developers)

**⚠️ 개발자 앱 승인 필요 (수일~수주 소요)**

1. [TikTok for Developers](https://developers.tiktok.com/) 접속
2. 앱 등록 → **Content Posting API** 권한 요청
3. 승인 후 OAuth 인증으로 액세스 토큰 발급

```env
TIKTOK_CLIENT_KEY=awxxxxxxxxxxxxxx
TIKTOK_CLIENT_SECRET=xxxxxxxxxxxxxx
TIKTOK_ACCESS_TOKEN=act.xxxxxxxxxxxxxx
```

---

## 사용법

### 기본 흐름

```bash
# 1. 내 채널에서 영상 다운로드 (오래된순 10개)
python main.py download

# 2. 모든 플랫폼에 업로드
python main.py upload

# 또는 한번에
python main.py all
```

### 세부 옵션

```bash
# 특정 채널에서 5개만 다운로드
python main.py download --channel-url https://www.youtube.com/@my_channel --max-videos 5

# YouTube와 TikTok만 업로드
python main.py upload --platforms youtube tiktok

# 이미 업로드된 영상 강제 재업로드
python main.py upload --force

# 저장 폴더 지정
python main.py all --download-dir ./my_videos
```

---

## 주의사항

| 항목 | 내용 |
|------|------|
| YouTube 일일 업로드 한도 | 기본 6회/일 (할당량 신청 시 늘릴 수 있음) |
| Instagram 릴스 | 최대 15분 / 비즈니스 계정 필수 |
| TikTok | 최대 60초 (일반) ~ 10분 (인증 계정) |
| 저작권 | 본인 채널 영상만 재업로드 권장 |

---

## 파일 구조

```
social-media-automation/
├── main.py                  # 메인 실행 파일
├── downloader.py            # YouTube 다운로드
├── uploaders/
│   ├── youtube_uploader.py  # YouTube 업로드
│   ├── instagram_uploader.py # Instagram 업로드
│   └── tiktok_uploader.py   # TikTok 업로드
├── requirements.txt
├── .env.example             # 환경변수 예시
├── .env                     # 실제 API 키 (git에 올리지 마세요!)
└── downloads/               # 다운로드된 영상 저장
    └── downloaded_videos.json  # 업로드 이력 추적
```
