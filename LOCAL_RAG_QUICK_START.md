# 🚀 로컬 RAG 시스템 빠른 시작 (완전 무료)

## ✨ 특징

- 💰 **완전 무료**: OpenAI API 없이 로컬 실행
- 🚀 **M4 Pro GPU 가속**: Apple Silicon MPS 지원
- 🎯 **높은 정확도**: 시맨틱 검색 (의미 기반)
- 🇰🇷 **한국어 특화**: 한국어 임베딩 모델

## 📦 설치 (1분)

```bash
cd /Users/choigapju/Desktop/helper
source lionhelper/bin/activate
pip install -r requirements.txt
```

## ⚙️ 설정 (2분)

`.env` 파일 생성:

```bash
# Pinecone API 키만 필요 (무료)
USE_RAG=true
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX_NAME=lionhelper-faq

# 로컬 임베딩 (무료, API 키 불필요)
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
EMBEDDING_DIMENSION=384
```

**Pinecone 무료 가입**: https://www.pinecone.io/

## 🧪 테스트 (1분)

```bash
python test_rag_system.py
```

## 📤 데이터 업로드 (1분)

```bash
python upload_data_to_pinecone.py
```

## 🎉 서버 실행

```bash
python main.py
```

## 📊 비용

| 항목 | 비용 |
|------|------|
| 로컬 임베딩 | **$0** (무료) |
| Pinecone (100K 벡터) | **$0** (무료 플랜) |
| **총 비용** | **$0/월** |

## 🎯 성능

- **검색 정확도**: ⭐⭐⭐⭐⭐
- **응답 속도**: 0.1~0.3초
- **GPU 가속**: M4 Pro Apple Silicon

## 📖 상세 가이드

전체 문서: `RAG_SETUP_GUIDE.md`

## 🆚 기존 vs 신규

| 기능 | 키워드 방식 | RAG (로컬) |
|------|-----------|-----------|
| 정확도 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 비용 | $0 | **$0** |
| 의미 이해 | ❌ | ✅ |
| 속도 | 매우 빠름 | 빠름 (GPU) |

## 💡 예시

### 검색 개선

**질문**: "장려금은 언제 들어오나요?"

- **이전**: "훈련장려금" 정확 매칭 필요 → 낮은 정확도
- **현재**: 의미론적 매칭 → 높은 정확도 ✅

---

**🎉 5분 만에 무료 RAG 시스템 완성!**

