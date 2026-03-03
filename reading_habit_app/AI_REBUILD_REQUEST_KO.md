# AI 재개발 요청서 (Reading Habit App)

## 1) 배경과 목표
- 기존 코드는 참고만 하고, 프로젝트를 처음부터 다시 구축한다.
- 목표는 **모바일 웹에 최적화된 독서 관리 웹앱**을 만드는 것이다.
- 핵심은 스마트폰 카메라 바코드 스캔으로 ISBN을 읽고, 알라딘 API로 도서 정보를 가져와 등록/기록/조회까지 한 흐름으로 완성하는 것이다.

## 2) 최종 산출물
- `frontend/`: Next.js (App Router, TypeScript) 기반 UI
- `backend/`: Flask 기반 REST API
- `README.md`: 로컬 실행, 환경변수, 배포 전 체크리스트
- `.env.example`: 필요한 키 목록

## 3) 필수 기능 요구사항
1. ISBN 스캔
- 스마트폰 카메라로 바코드 인식
- 인식 값이 ISBN-10/13이 아니면 사용자에게 오류 메시지
- 스캔 성공 시 자동으로 검색/등록 화면으로 이동

2. 알라딘 API 도서 조회
- ISBN 또는 제목/저자 키워드로 검색
- 도서 제목, 저자, 출판사, 출간일, 표지, ISBN13, 설명 표시
- 결과가 없을 때 빈 상태 UI 제공

3. 책 등록
- 사용자가 독서 목표(예: 완독, 요약 작성, 업무 적용)를 선택/입력
- 등록 완료 시 세션 또는 DB에 현재 읽는 책 저장

4. 독서 기록
- 일일 기록(읽은 페이지/시간/메모) 저장
- AI 피드백(요약, 동기부여, 다음 액션 제안) 생성

5. 내 서재
- 등록된 책 목록 조회
- 최근 기록, 누적 독서량, 간단한 통계 표시

6. 내보내기
- 현재 독서 노트를 Markdown으로 다운로드

## 4) UI/UX 요구사항
- 첨부한 레퍼런스 이미지 스타일을 최대한 반영한다.
- 사이드바 문구는 아래로 고정:
  - `Category` -> `책 등록`
  - `My Library` -> `내 서재`
- 메인 구조:
  - 좌측: 사이드바
  - 중앙: 검색/추천/카드 영역
  - 상단: 사용자 영역
- 모바일 최적화:
  - 390px 기준에서도 주요 기능(스캔, 검색, 등록, 기록)이 3탭 이내 접근 가능
  - 버튼/입력창 터치 영역 최소 44px
  - 카메라 권한 실패 시 대체 입력(ISBN 수동 입력) 제공

## 5) 기술 요구사항
- Frontend: Next.js App Router + TypeScript
- Backend: Flask + SQLite
- API 통신: JSON, `credentials: include` 사용 가능 구조
- 외부 API:
  - Aladin Open API
  - Gemini API (선택: 피드백/요약)
- 품질:
  - 에러 처리(네트워크 실패, API 키 누락, 권한 거부) 명확히 표시
  - 로딩/빈 상태/실패 상태 UI 각각 구현

## 6) 권장 API 설계
- `GET /api/v1/search?q=...&query_type=Title|Author|ISBN13`
- `GET /api/isbn/:isbn`
- `POST /api/v1/register`
- `POST /api/v1/log`
- `GET /api/v1/bookshelf`
- `GET /api/v1/session`
- `GET /export`

## 7) 완료 기준 (Acceptance Criteria)
1. iPhone Safari에서 카메라 스캔으로 ISBN 인식 가능
2. ISBN 인식 후 알라딘 API 조회 결과가 3초 내 표시(일반 네트워크 기준)
3. 책 등록 -> 독서 기록 -> 내 서재 반영까지 데이터 흐름 정상 동작
4. 사이드바 라벨이 `책 등록`, `내 서재`로 반영
5. 데스크톱/모바일 반응형 레이아웃 깨짐 없음
6. README만 보고 초기 실행 가능

## 8) 환경변수 예시
```env
# backend
FLASK_SECRET_KEY=change_me
ALADIN_TTB_KEY=your_aladin_ttb_key
GEMINI_API_KEY=your_gemini_api_key
FRONTEND_ORIGINS=http://localhost:3000

# frontend (.env.local)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8501
```

## 9) AI에게 바로 전달할 실행 프롬프트
아래 프롬프트를 그대로 전달:

```text
기존 코드는 참고만 하고, 프로젝트를 처음부터 재구축해주세요.

[목표]
- 스마트폰 카메라 바코드 스캔으로 ISBN을 읽고,
- 알라딘 API로 책 정보를 조회하여 등록/독서기록/내서재 조회까지 가능한 웹앱을 만듭니다.

[기술]
- Frontend: Next.js(App Router, TypeScript)
- Backend: Flask + SQLite
- API: JSON 기반

[필수 기능]
1) ISBN 스캔(모바일 카메라, 실패 시 수동입력 대체)
2) 알라딘 API 검색(ISBN/제목/저자)
3) 책 등록(독서 목표 포함)
4) 일일 독서 기록 저장 + AI 피드백
5) 내 서재 목록/기본 통계
6) Markdown 내보내기

[UI/UX]
- 첨부된 레퍼런스 이미지 스타일을 반영
- 사이드바 라벨 변경:
  - Category -> 책 등록
  - My Library -> 내 서재
- 모바일(아이폰) 우선 반응형으로 구현

[산출물]
- frontend/, backend/, README.md, .env.example
- 로컬 실행 명령어와 환경변수 설정을 README에 명확히 작성

[완료 조건]
- iPhone Safari 기준 바코드 스캔 동작
- 스캔 -> 검색 -> 등록 -> 기록 -> 내서재 흐름이 끊김 없이 동작
- 에러/로딩/빈 상태 UI 구현
```

