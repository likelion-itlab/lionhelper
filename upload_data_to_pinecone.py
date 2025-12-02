#!/usr/bin/env python3
"""
FAQ 데이터를 Pinecone에 업로드하는 스크립트

사용법:
    python upload_data_to_pinecone.py [--force]
    
옵션:
    --force: 기존 데이터를 삭제하고 강제로 다시 업로드
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_ENVIRONMENT,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION
)
from ai.embeddings import EmbeddingClient
from ai.pinecone_client import PineconeClient
from ai.data_loader import load_and_upload_to_pinecone

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='FAQ 데이터를 Pinecone에 업로드')
    parser.add_argument('--force', action='store_true', help='기존 데이터를 삭제하고 강제로 다시 업로드')
    parser.add_argument('--xlsx', type=str, default='ITLab_FAQ.xlsx', help='XLSX 파일 경로')
    args = parser.parse_args()
    
    # API 키 확인
    if not PINECONE_API_KEY or PINECONE_API_KEY == "":
        logger.error("PINECONE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)
    
    logger.info(f"✅ 로컬 임베딩 모델 사용 (무료): {EMBEDDING_MODEL}")
    
    # XLSX 파일 경로 확인
    xlsx_path = args.xlsx
    if not os.path.isabs(xlsx_path):
        xlsx_path = os.path.join(os.path.dirname(__file__), xlsx_path)
    
    if not os.path.exists(xlsx_path):
        logger.error(f"XLSX 파일을 찾을 수 없습니다: {xlsx_path}")
        sys.exit(1)
    
    logger.info(f"XLSX 파일: {xlsx_path}")
    logger.info(f"강제 재업로드: {args.force}")
    
    try:
        # 로컬 임베딩 클라이언트 초기화 (무료, API 키 불필요)
        logger.info("로컬 임베딩 클라이언트 초기화...")
        logger.info("⏳ 첫 실행 시 모델 다운로드 (약 100MB~500MB)...")
        embedding_client = EmbeddingClient(model=EMBEDDING_MODEL)
        
        # Pinecone 클라이언트 초기화
        logger.info("Pinecone 클라이언트 초기화...")
        pinecone_client = PineconeClient(
            api_key=PINECONE_API_KEY,
            index_name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            environment=PINECONE_ENVIRONMENT
        )
        
        # 데이터 업로드
        logger.info("데이터 업로드 시작...")
        result = load_and_upload_to_pinecone(
            xlsx_path=xlsx_path,
            embedding_client=embedding_client,
            pinecone_client=pinecone_client,
            force_reload=args.force
        )
        
        # 결과 출력
        logger.info("=" * 60)
        logger.info(f"업로드 결과: {result['status']}")
        logger.info(f"메시지: {result['message']}")
        logger.info(f"벡터 개수: {result['vector_count']}")
        logger.info("=" * 60)
        
        if result['status'] == 'success':
            logger.info("✅ 데이터 업로드 완료!")
            sys.exit(0)
        else:
            logger.error("❌ 데이터 업로드 실패!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

