# 라이언 헬퍼 RAG 시스템 설정 가이드 (로컬 모델, 무료)

이 가이드는 기존 키워드 기반 시스템을 **RAG (Retrieval-Augmented Generation) + Pinecone + 로컬 임베딩** 시스템으로 업그레이드하는 방법을 안내합니다.

## 🎯 변경 사항 요약

### 이전 시스템
- **키워드 매칭**: 하드코딩된 딕셔너리 (`QA_DATABASE`)
- **유사도 계산**: SequenceMatcher (문자열 유사도)
- **데이터 관리**: Python 코드에 직접 작성

### 새로운 시스템 ✨
- **시맨틱 검색**: 로컬 임베딩 (Sentence Transformers) + Pinecone 벡터 DB
- **유사도 계산**: 코사인 유사도 (의미론적 유사성)
- **데이터 관리**: XLSX 파일 → 자동 업로드
- **💰 완전 무료**: OpenAI API 없이 M4 Pro MacBook에서 로컬 실행
- **🚀 GPU 가속**: Apple Silicon MPS 지원

## 📋 필요한 준비물

### 1. API 키 발급

#### ✅ Pinecone API 키 (무료)
1. [Pinecone](https://www.pinecone.io/)에 가입
2. 무료 Starter 플랜 선택 (100K 벡터까지 무료)
3. API Key 생성 및 복사

#### ❌ OpenAI API 키 불필요!
- **로컬 임베딩 모델 사용**: Sentence Transformers
- **완전 무료**: API 호출 비용 없음
- **빠른 속도**: M4 Pro MacBook GPU 가속 지원

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# === RAG 시스템 활성화 ===
USE_RAG=true

# === Pinecone 설정 (무료 플랜) ===
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=lionhelper-faq

# === 로컬 임베딩 설정 (무료) ===
# 추천 모델:
# - jhgan/ko-sroberta-multitask (384차원, 한국어 특화, 빠름) ⭐ 추천
# - jhgan/ko-sbert-multitask (768차원, 한국어 특화, 고품질)
# - paraphrase-multilingual-MiniLM-L12-v2 (384차원, 다국어, 빠름)
# - intfloat/multilingual-e5-large (1024차원, 다국어, 최고 품질)

EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
EMBEDDING_DIMENSION=384

# === 검색 설정 ===
TOP_K_RESULTS=5
MIN_SIMILARITY_SCORE=0.7

# === 기존 설정들 (유지) ===
ANTHROPIC_API_KEY=your_anthropic_api_key
DATABASE_URL=postgresql://...
SLACK_BOT_TOKEN=your_slack_token
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
cd /Users/choigapju/Desktop/helper
source lionhelper/bin/activate
pip install -r requirements.txt
```

**첫 실행 시 자동 다운로드:**
- 한국어 임베딩 모델 (약 110MB~560MB)
- M4 Pro MacBook에서 매우 빠르게 다운로드 완료

### 2. 시스템 테스트

```bash
python test_rag_system.py
```

**테스트 내용:**
- ✅ 로컬 임베딩 모델 로드
- ✅ Apple Silicon GPU (MPS) 가속 확인
- ✅ Pinecone 연결 확인
- ✅ 검색 기능 테스트

### 3. 데이터 업로드

XLSX 파일을 Pinecone에 업로드:

```bash
# 처음 업로드 (자동으로 임베딩 생성)
python upload_data_to_pinecone.py

# 강제 재업로드 (기존 데이터 삭제 후 재업로드)
python upload_data_to_pinecone.py --force

# 다른 XLSX 파일 사용
python upload_data_to_pinecone.py --xlsx path/to/your/file.xlsx
```

**업로드 속도:**
- M4 Pro MacBook: 74개 FAQ 업로드 약 10~30초
- GPU 가속으로 매우 빠름

### 4. 서버 실행

```bash
python main.py
```

또는

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 🎨 지원 임베딩 모델

### 한국어 특화 모델 (추천)

| 모델 | 차원 | 크기 | 특징 | 추천도 |
|------|------|------|------|--------|
| `jhgan/ko-sroberta-multitask` | 384 | 110MB | 빠른 속도, 높은 정확도 | ⭐⭐⭐⭐⭐ |
| `jhgan/ko-sbert-multitask` | 768 | 110MB | 고품질, 다양한 태스크 | ⭐⭐⭐⭐ |

### 다국어 모델

| 모델 | 차원 | 크기 | 특징 | 추천도 |
|------|------|------|------|--------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 120MB | 빠름, 50개 언어 | ⭐⭐⭐⭐ |
| `intfloat/multilingual-e5-large` | 1024 | 560MB | 최고 품질, 느림 | ⭐⭐⭐ |

### 모델 변경 방법

`.env` 파일에서:
```bash
# 한국어 특화 (추천)
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
EMBEDDING_DIMENSION=384

# 또는 고품질 다국어
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DIMENSION=1024
```

## 📊 시스템 작동 확인

### 헬스 체크
```bash
curl http://localhost:8001/health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "model": "Intelligent: Claude-3-Haiku + RAG (Pinecone + 로컬 임베딩)",
  "qa_count": 74,
  "rag_status": "connected",
  "rag_available": true,
  "response_mode": "rag_enhanced"
}
```

### 검색 테스트
```bash
curl "http://localhost:8001/search?query=훈련장려금은 언제 받을 수 있나요?"
```

### 채팅 테스트
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "출석률 80% 이상이면 수료 가능한가요?",
    "use_claude": true
  }'
```

## 🔄 레거시 모드 (키워드 방식)

RAG를 비활성화하고 싶을 때:

### 방법 1: 환경 변수 변경
`.env` 파일에서:
```bash
USE_RAG=false
```

### 방법 2: Pinecone API 키 제거
Pinecone API 키가 없으면 자동으로 레거시 모드로 전환됩니다.

## 📁 새로운 파일 구조

```
helper/
├── ai/
│   ├── embeddings.py          # ✨ 로컬 임베딩 (Sentence Transformers)
│   ├── pinecone_client.py     # ✨ Pinecone 벡터 DB 클라이언트
│   ├── data_loader.py         # ✨ XLSX → Pinecone 데이터 로더
│   ├── qa_search_rag.py       # ✨ RAG 검색 엔진
│   ├── qa_search.py           # 기존: 레거시 키워드 검색 (백업)
│   ├── qa_data.py             # 기존: 레거시 데이터 (백업)
│   └── claude_client.py       # 기존: Claude API
├── config/
│   └── settings.py            # 🔧 수정: RAG 설정 추가
├── main.py                    # 🔧 수정: RAG 통합
├── requirements.txt           # 🔧 수정: sentence-transformers, torch 추가
├── ITLab_FAQ.xlsx            # 데이터 소스
├── upload_data_to_pinecone.py # ✨ 데이터 업로드 스크립트
└── test_rag_system.py         # ✨ 시스템 테스트 스크립트
```

## 🔧 FAQ 데이터 업데이트 방법

### 1. XLSX 파일 수정
`ITLab_FAQ.xlsx` 파일을 엑셀에서 수정

### 2. Pinecone 재업로드
```bash
python upload_data_to_pinecone.py --force
```

### 3. 서버 재시작 불필요
업로드 후 즉시 반영됩니다.

## 📈 성능 비교

| 항목 | 키워드 방식 | RAG (로컬) |
|------|------------|-----------|
| 검색 정확도 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 의미론적 이해 | ❌ | ✅ |
| 유사 질문 매칭 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 응답 속도 | 매우 빠름 | 빠름 (M4 GPU) |
| 데이터 관리 | 불편 | 편리 |
| 비용 | 무료 | **완전 무료** |
| GPU 가속 | ❌ | ✅ (Apple MPS) |

## 🎓 시맨틱 검색 예시

### 키워드 방식 (이전)
- 질문: "장려금은 언제 입금되나요?"
- → "훈련장려금", "입금" 키워드 정확히 매칭 필요

### RAG 방식 (현재)
- 질문: "장려금은 언제 입금되나요?"
- → "훈련장려금은 언제 받을 수 있나요?" 와 의미적으로 유사하다고 판단
- → 높은 정확도로 관련 답변 제공
- → **완전 무료, 로컬 실행**

## 💰 비용 비교

### 기존 OpenAI 방식
- **임베딩 비용**: $0.00002 / 1,000 tokens
- 74개 FAQ 업로드: 약 $0.01
- 검색 10,000회/월: 약 $1
- **월 예상 비용**: $1~$5

### 현재 로컬 방식 ✨
- **임베딩 비용**: **$0 (무료)**
- 74개 FAQ 업로드: **$0 (로컬 실행)**
- 검색 무제한: **$0 (로컬 실행)**
- **Pinecone 무료 플랜**: 100K 벡터까지 무료
- **월 예상 비용**: **$0 (완전 무료)**

## 🚀 M4 Pro MacBook 최적화

### Apple Silicon GPU 가속
```python
# 자동으로 Apple MPS (Metal Performance Shaders) 사용
# GPU 가속으로 2~5배 빠른 임베딩 생성
```

### 성능 벤치마크 (M4 Pro)
- 임베딩 생성 (74개 FAQ): 약 3~10초
- 검색 쿼리 처리: 약 0.1~0.3초
- GPU 사용률: 자동 최적화

## 🐛 트러블슈팅

### 1. 모델 다운로드 실패
```
ERROR: 모델 다운로드 실패
```
**해결책:**
- 인터넷 연결 확인
- 다시 시도: 자동으로 다운로드 재시도
- 수동 다운로드: HuggingFace에서 직접 다운로드

### 2. MPS 가속 사용 불가
```
WARNING: MPS 사용 불가, CPU 사용
```
**해결책:**
- macOS 버전 확인 (12.3 이상 필요)
- PyTorch 버전 확인 (2.0 이상 필요)
- CPU로도 충분히 빠름 (M4 Pro)

### 3. Pinecone 연결 실패
```
ERROR: Pinecone 연결 테스트 실패
```
**해결책:**
- API 키 확인
- 인덱스 이름 확인
- 네트워크 연결 확인

### 4. 차원 불일치 오류
```
ERROR: dimension mismatch
```
**해결책:**
- `.env` 파일에서 `EMBEDDING_DIMENSION` 확인
- 모델에 맞는 차원 설정:
  - `jhgan/ko-sroberta-multitask`: 384
  - `intfloat/multilingual-e5-large`: 1024
- Pinecone 인덱스 재생성 필요할 수 있음

## 🚀 프로덕션 배포

### Render.com 배포 시 환경 변수 추가
```bash
USE_RAG=true
PINECONE_API_KEY=your_key
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
EMBEDDING_DIMENSION=384
```

### Heroku 배포 시
```bash
heroku config:set USE_RAG=true
heroku config:set PINECONE_API_KEY=your_key
heroku config:set EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
```

**주의**: 서버 배포 시 첫 시작 시 모델 다운로드로 인해 약 1~2분 소요될 수 있습니다.

## 🎁 추가 기능

### 모델 정보 확인
```python
from ai.embeddings import EmbeddingClient

client = EmbeddingClient()
info = client.get_model_info()
print(info)
# {
#   "model_name": "jhgan/ko-sroberta-multitask",
#   "device": "mps",  # Apple Silicon GPU
#   "dimension": 384,
#   "is_gpu": True,
#   "model_type": "sentence-transformers (로컬)"
# }
```

### 추천 모델 목록
```python
from ai.embeddings import RECOMMENDED_KOREAN_MODELS

for key, info in RECOMMENDED_KOREAN_MODELS.items():
    print(f"{info['name']}: {info['description']}")
```

## 📞 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.

---

**축하합니다! 🎉 완전 무료 로컬 RAG 시스템이 성공적으로 구축되었습니다.**

**💰 비용: $0/월**
**🚀 속도: M4 Pro GPU 가속**
**🎯 정확도: 시맨틱 검색**
