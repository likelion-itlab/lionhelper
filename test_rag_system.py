#!/usr/bin/env python3
"""
RAG 시스템 테스트 스크립트

사용법:
    python test_rag_system.py
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    PINECONE_API_KEY,
    USE_RAG,
    EMBEDDING_MODEL
)

print("=" * 60)
print("🔍 RAG 시스템 테스트 (로컬 모델, 무료)")
print("=" * 60)

# 1. 환경 변수 확인
print("\n1️⃣  환경 변수 확인")
print(f"   USE_RAG: {USE_RAG}")
print(f"   PINECONE_API_KEY: {'✅ 설정됨' if PINECONE_API_KEY else '❌ 없음'}")
print(f"   로컬 임베딩 모델: {EMBEDDING_MODEL} (무료)")
print(f"   M4 Pro MacBook GPU 가속: Apple Silicon MPS 지원")

if not PINECONE_API_KEY:
    print("\n⚠️  PINECONE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    sys.exit(1)

# 2. 클라이언트 초기화
print("\n2️⃣  클라이언트 초기화")
try:
    from ai.embeddings import EmbeddingClient
    from ai.pinecone_client import PineconeClient
    from ai.qa_search_rag import RAGSearchEngine
    from config.settings import (
        PINECONE_INDEX_NAME,
        PINECONE_ENVIRONMENT,
        EMBEDDING_MODEL,
        EMBEDDING_DIMENSION
    )
    
    print("   로컬 임베딩 클라이언트 초기화 중...")
    print("   ⏳ 첫 실행 시 모델 다운로드 (약 100MB~500MB)...")
    embedding_client = EmbeddingClient(model=EMBEDDING_MODEL)
    print("   ✅ 로컬 임베딩 클라이언트 초기화 완료 (무료)")
    
    print("   Pinecone 클라이언트 초기화 중...")
    pinecone_client = PineconeClient(
        api_key=PINECONE_API_KEY,
        index_name=PINECONE_INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        environment=PINECONE_ENVIRONMENT
    )
    print("   ✅ Pinecone 클라이언트 초기화 완료")
    
    print("   RAG 검색 엔진 초기화 중...")
    rag_engine = RAGSearchEngine(embedding_client, pinecone_client)
    print("   ✅ RAG 검색 엔진 초기화 완료")
    
except Exception as e:
    print(f"   ❌ 초기화 실패: {str(e)}")
    sys.exit(1)

# 3. 연결 테스트
print("\n3️⃣  시스템 테스트")
try:
    print("   로컬 임베딩 모델 테스트...")
    if embedding_client.test_connection():
        model_info = embedding_client.get_model_info()
        print("   ✅ 임베딩 모델 정상 작동")
        print(f"      - 모델: {model_info['model_name']}")
        print(f"      - 디바이스: {model_info['device']}")
        print(f"      - GPU 가속: {'✅' if model_info['is_gpu'] else '❌'}")
        print(f"      - 차원: {model_info['dimension']}")
    else:
        print("   ❌ 임베딩 모델 테스트 실패")
        sys.exit(1)
    
    print("   Pinecone 연결 테스트...")
    if pinecone_client.test_connection():
        print("   ✅ Pinecone 연결 성공")
    else:
        print("   ❌ Pinecone 연결 실패")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ 연결 테스트 실패: {str(e)}")
    sys.exit(1)

# 4. 인덱스 통계
print("\n4️⃣  Pinecone 인덱스 통계")
try:
    stats = pinecone_client.get_index_stats()
    print(f"   벡터 개수: {stats['total_vector_count']}")
    print(f"   차원 수: {stats['dimension']}")
    print(f"   인덱스 사용률: {stats['index_fullness']:.2%}")
    
    if stats['total_vector_count'] == 0:
        print("\n   ⚠️  벡터가 없습니다. 데이터를 업로드하세요:")
        print("   python upload_data_to_pinecone.py")
        
except Exception as e:
    print(f"   ❌ 통계 조회 실패: {str(e)}")

# 5. 검색 테스트
print("\n5️⃣  검색 테스트")
test_queries = [
    "훈련장려금은 언제 받을 수 있나요?",
    "출석률 80% 이상이면 수료 가능한가요?",
    "줌 배경 화면 설정 방법"
]

for query in test_queries:
    print(f"\n   질문: {query}")
    try:
        results = rag_engine.search(query, top_k=3, min_score=0.6)
        
        if results:
            print(f"   검색 결과: {len(results)}개")
            for i, result in enumerate(results, 1):
                print(f"      {i}. 질문: {result['question'][:50]}...")
                print(f"         유사도: {result['score']:.4f}")
                print(f"         카테고리: {result['category']}")
        else:
            print("   검색 결과 없음")
            
    except Exception as e:
        print(f"   ❌ 검색 실패: {str(e)}")

# 6. 임베딩 테스트
print("\n6️⃣  임베딩 테스트")
try:
    test_text = "테스트 텍스트"
    embedding = embedding_client.create_embedding(test_text)
    print(f"   임베딩 차원: {len(embedding)}")
    print(f"   임베딩 샘플: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
    print("   ✅ 임베딩 생성 성공")
except Exception as e:
    print(f"   ❌ 임베딩 생성 실패: {str(e)}")

# 최종 결과
print("\n" + "=" * 60)
print("✅ RAG 시스템 테스트 완료!")
print("=" * 60)
print("\n다음 명령어로 서버를 시작하세요:")
print("   python main.py")
print("\n또는:")
print("   uvicorn main:app --host 0.0.0.0 --port 8001 --reload")

