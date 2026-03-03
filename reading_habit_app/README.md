# Reading Habit App (AI 독서 비서)

독서 목표를 정하고, 책 정보를 등록한 뒤, 매일 독서 기록과 AI 피드백을 남길 수 있는 앱입니다.  
현재 구조는 **Flask 백엔드 + Next.js 프론트엔드**로 분리되어 있습니다.

## 주요 기능

- 스마트폰 카메라로 바코드 스캔 후 ISBN 자동 인식
- 알라딘 API 기반 제목/저자/ISBN 검색
- AI 독서 큐레이션 생성 (목표 기반)
- 일일 독서 기록 저장 및 AI 피드백 생성
- 책장 보기 및 Markdown 독서노트 내보내기

## 기술 스택

- Backend: Flask
- Frontend: Next.js (App Router, TypeScript)
- Database: SQLite (`reading_habit.db`)
- External APIs:
  - 알라딘 Open API (도서 검색)
  - Google Gemini API (큐레이션/피드백/표지 분석)
  - ZXing (`@zxing/library`) (바코드 스캔)

## 요구 사항

- Python 3.9+
- Node.js 20+
- 인터넷 연결 (알라딘/Gemini/ZXing 사용)

## 설치

### 1) Python 백엔드

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask requests python-dotenv google-generativeai pillow
```

### 2) Next.js 프론트엔드

```bash
cd frontend
npm install
```

## 환경 변수

프로젝트 루트 `.env` 예시:

```env
FLASK_SECRET_KEY=your_secret_key
ALADIN_TTB_KEY=your_aladin_ttb_key
GEMINI_API_KEY=your_gemini_api_key
FRONTEND_ORIGINS=http://localhost:3000
```

프론트엔드 환경 변수 (`frontend/.env.local`):

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8501
```

## 실행

### 터미널 1: Flask API 서버

```bash
python3 app.py
```

- 기본 주소: `http://localhost:8501`

### 터미널 2: Next.js 프론트

```bash
cd frontend
npm run dev
```

- 기본 주소: `http://localhost:3000`

## API 개요 (Next 연동용)

- `GET /api/v1/home`
- `GET /api/v1/session`
- `GET /api/v1/search?q=...&query_type=Title|Author|ISBN13`
- `POST /api/v1/register`
- `POST /api/v1/log`
- `GET /api/v1/bookshelf`
- `GET /api/isbn/<isbn>`
- `GET /export` (Markdown 파일 다운로드)

## 디렉터리 구조

```text
reading_habit_app/
├── app.py
├── backend/
│   ├── ai_service.py
│   ├── book_service.py
│   └── db_service.py
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── templates/  # 기존 Flask 템플릿(레거시)
├── static/
└── README.md
```

## 참고 사항

- Next.js 프론트는 `credentials: include`로 Flask 세션 쿠키를 사용합니다.
- CORS 허용 대상은 `FRONTEND_ORIGINS` 환경 변수로 제어합니다.
- 모바일 카메라 스캔은 `https` 또는 `localhost` 환경에서 안정적으로 동작합니다.
