"""
Pinecone 벡터 데이터베이스 클라이언트
"""
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import time

logger = logging.getLogger(__name__)


class PineconeClient:
    """Pinecone 벡터 DB 클라이언트"""
    
    def __init__(self, api_key: str, index_name: str, dimension: int = 1536, environment: str = "gcp-starter"):
        """
        Pinecone 클라이언트 초기화
        
        Args:
            api_key: Pinecone API 키
            index_name: 인덱스 이름
            dimension: 임베딩 벡터 차원 수
            environment: Pinecone 환경
        """
        if not api_key:
            raise ValueError("Pinecone API 키가 제공되지 않았습니다.")
        
        self.api_key = api_key
        self.index_name = index_name
        self.dimension = dimension
        self.environment = environment
        
        # Pinecone 클라이언트 초기화
        self.pc = Pinecone(api_key=api_key)
        self.index = None
        
        # 인덱스 초기화
        self._initialize_index()
        
        logger.info(f"PineconeClient 초기화 완료 (인덱스: {index_name}, 차원: {dimension})")
    
    def _initialize_index(self):
        """인덱스 초기화 (없으면 생성)"""
        try:
            # 기존 인덱스 목록 확인
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"인덱스 '{self.index_name}'가 없습니다. 새로 생성합니다...")
                
                # 새 인덱스 생성
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                
                # 인덱스 생성 대기
                logger.info("인덱스 생성 중... (최대 60초 대기)")
                time.sleep(10)
                
                # 인덱스 준비 확인
                max_retries = 30
                for i in range(max_retries):
                    try:
                        desc = self.pc.describe_index(self.index_name)
                        if desc.status.ready:
                            logger.info("인덱스 생성 완료!")
                            break
                    except:
                        pass
                    time.sleep(2)
                    if i == max_retries - 1:
                        logger.warning("인덱스 준비 확인 시간 초과")
            else:
                logger.info(f"기존 인덱스 '{self.index_name}' 사용")
            
            # 인덱스 연결
            self.index = self.pc.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"인덱스 초기화 실패: {str(e)}")
            raise
    
    def upsert_vectors(self, vectors: List[Dict[str, Any]], namespace: str = ""):
        """
        벡터 업로드 (업데이트 또는 삽입)
        
        Args:
            vectors: 벡터 데이터 리스트
                    [{"id": "1", "values": [...], "metadata": {...}}, ...]
            namespace: 네임스페이스 (선택사항)
        """
        try:
            if not self.index:
                raise ValueError("인덱스가 초기화되지 않았습니다.")
            
            # 배치 처리 (최대 100개씩)
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
                logger.info(f"벡터 업로드 진행: {min(i + batch_size, len(vectors))}/{len(vectors)}")
            
            logger.info(f"총 {len(vectors)}개 벡터 업로드 완료")
            
        except Exception as e:
            logger.error(f"벡터 업로드 실패: {str(e)}")
            raise
    
    def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        namespace: str = "",
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        유사도 검색 수행
        
        Args:
            query_vector: 쿼리 벡터
            top_k: 반환할 결과 개수
            namespace: 네임스페이스
            filter_dict: 메타데이터 필터
            include_metadata: 메타데이터 포함 여부
            
        Returns:
            검색 결과 리스트
        """
        try:
            if not self.index:
                raise ValueError("인덱스가 초기화되지 않았습니다.")
            
            # Pinecone 쿼리 실행
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter_dict,
                include_metadata=include_metadata
            )
            
            # 결과 파싱
            matches = []
            for match in results.matches:
                match_dict = {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {}
                }
                matches.append(match_dict)
            
            logger.info(f"검색 완료: {len(matches)}개 결과 반환")
            return matches
            
        except Exception as e:
            logger.error(f"검색 실패: {str(e)}")
            raise
    
    def delete_all(self, namespace: str = ""):
        """
        모든 벡터 삭제
        
        Args:
            namespace: 네임스페이스
        """
        try:
            if not self.index:
                raise ValueError("인덱스가 초기화되지 않았습니다.")
            
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"네임스페이스 '{namespace}' 모든 벡터 삭제 완료")
            
        except Exception as e:
            logger.error(f"벡터 삭제 실패: {str(e)}")
            raise
    
    def get_index_stats(self, namespace: str = "") -> Dict[str, Any]:
        """
        인덱스 통계 조회
        
        Args:
            namespace: 네임스페이스
            
        Returns:
            인덱스 통계 정보
        """
        try:
            if not self.index:
                raise ValueError("인덱스가 초기화되지 않았습니다.")
            
            stats = self.index.describe_index_stats()
            
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Pinecone 연결 테스트
        
        Returns:
            연결 성공 여부
        """
        try:
            stats = self.get_index_stats()
            logger.info(f"Pinecone 연결 성공: {stats}")
            return True
        except Exception as e:
            logger.error(f"Pinecone 연결 테스트 실패: {str(e)}")
            return False

