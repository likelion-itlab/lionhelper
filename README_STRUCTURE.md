# 프로젝트 구조 설명

## 📁 디렉토리 구조

```
helper/
├── main.py                 # 메인 FastAPI 애플리케이션 (708줄, 기존 3424줄에서 80% 감소)
├── main_backup.py          # 기존 코드 백업
│
├── config/                 # ⚙️ 설정 관리
│   ├── __init__.py
│   └── settings.py         # 환경 변수 및 설정값
│
├── models/                 # 📋 데이터 모델
│   ├── __init__.py
│   └── schemas.py          # Pydantic 모델 정의
│
├── database/               # 💾 데이터베이스
│   ├── __init__.py
│   ├── connection.py       # DB 연결 관리
│   ├── init.py             # DB 초기화
│   └── operations.py       # CRUD 작업
│
├── ai/                     # 🤖 AI 모듈
│   ├── __init__.py
│   ├── claude_client.py    # Claude API 클라이언트
│   ├── qa_data.py          # QA 데이터베이스 (47개 항목)
│   └── qa_search.py        # QA 검색 및 매칭 로직
│
├── services/               # 🔧 비즈니스 로직
│   ├── __init__.py
│   ├── chat_service.py     # 채팅 서비스
│   ├── slack_service.py    # 슬랙 연동
│   └── feedback_service.py # 피드백 시스템
│
├── auth/                   # 🔐 인증
│   ├── __init__.py
│   └── jwt_handler.py      # JWT 토큰 처리
│
├── api/                    # 🌐 API 엔드포인트 (main.py에 인라인으로 정의)
│   └── __init__.py
│
└── static/                 # 🎨 정적 파일
    └── index.html
```

## 🎯 주요 개선 사항

### 1. 코드 분리 및 모듈화
- **기존**: 3424줄의 단일 파일
- **개선**: 기능별로 분리된 모듈 구조
- **결과**: 80% 코드 감소 (708줄)

### 2. 관심사의 분리 (Separation of Concerns)
각 모듈이 명확한 책임을 가짐:

#### `config/` - 설정 관리
- 환경 변수 중앙 관리
- JWT, API 키, 데이터베이스 설정

#### `models/` - 데이터 모델
- Pydantic 스키마 정의
- Request/Response 모델

#### `database/` - 데이터베이스
- 연결 관리
- CRUD 작업
- 초기화 로직

#### `ai/` - AI 관련 기능
- Claude API 클라이언트
- QA 데이터베이스 (47개 항목)
- 검색 및 매칭 알고리즘

#### `services/` - 비즈니스 로직
- 채팅 서비스 (Claude + 키워드)
- 슬랙 연동
- 피드백 시스템

#### `auth/` - 인증
- JWT 토큰 검증
- 사용자 인증

#### `main.py` - FastAPI 애플리케이션
- API 엔드포인트 정의
- 미들웨어 설정
- 앱 초기화

## 🚀 실행 방법

```bash
# 가상환경 활성화 (이미 있는 경우)
source lionhelper/bin/activate

# 서버 실행
python main.py

# 또는
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 📦 의존성

모든 의존성은 기존 `requirements.txt`와 동일합니다:
- fastapi
- uvicorn
- anthropic (Claude API)
- psycopg2 (PostgreSQL)
- slack-sdk
- jose (JWT)
- passlib (비밀번호 해싱)
- pydantic

## 🔄 마이그레이션 가이드

### 기존 코드 복원이 필요한 경우
```bash
# 백업 파일로 복원
cp main_backup.py main.py
```

### 새 구조 유지
현재 구조가 정상 작동하면 백업 파일 삭제:
```bash
rm main_backup.py
```

## 🧪 테스트

### API 엔드포인트 테스트
```bash
# 헬스체크
curl http://localhost:8001/health

# 채팅 테스트
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "훈련장려금은 얼마인가요?", "use_claude": true}'

# 검색 테스트
curl "http://localhost:8001/search?query=훈련장려금&limit=5"
```

## 📝 주요 API 엔드포인트

### 채팅
- `POST /chat` - AI 챗봇과 대화

### 검색
- `GET /search` - 키워드 검색
- `GET /qa-list` - QA 목록 조회

### 세션 관리
- `POST /sessions` - 새 세션 생성
- `GET /sessions` - 세션 목록
- `GET /sessions/{id}/messages` - 메시지 조회
- `DELETE /sessions/{id}` - 세션 삭제

### 슬랙
- `POST /slack/sync` - 슬랙 동기화
- `GET /slack/issues` - 이슈 목록
- `GET /slack/issues/stats` - 이슈 통계

### 피드백
- `POST /feedback` - 피드백 제출
- `GET /feedback/analysis` - 피드백 분석
- `GET /improvement/suggestions` - 개선 제안

### 헬스체크
- `GET /health` - 서버 상태 확인
- `GET /info` - 시스템 정보
- `GET /` - 메인 페이지

## 💡 장점

1. **유지보수성 향상**: 기능별로 분리되어 수정이 용이
2. **재사용성**: 각 모듈을 독립적으로 사용 가능
3. **테스트 용이성**: 각 모듈을 개별적으로 테스트 가능
4. **확장성**: 새로운 기능 추가가 쉬움
5. **가독성**: 코드 구조가 명확하고 이해하기 쉬움

## 🐛 문제 해결

### Import 오류 발생 시
```bash
# Python 경로 확인
export PYTHONPATH=/Users/choigapju/Desktop/helper:$PYTHONPATH
python main.py
```

### 데이터베이스 연결 오류
- `config/settings.py`에서 데이터베이스 설정 확인
- PostgreSQL 서버 실행 상태 확인

### Claude API 오류
- `ANTHROPIC_API_KEY` 환경 변수 설정 확인
- API 키 유효성 확인

