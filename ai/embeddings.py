"""
임베딩 생성 모듈 - Sentence Transformers (로컬 실행, 무료)
"""
import logging
from typing import List, Union
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """로컬 임베딩 생성 클라이언트 (Sentence Transformers)"""
    
    def __init__(self, model: str = "jhgan/ko-sroberta-multitask"):
        """
        임베딩 클라이언트 초기화
        
        Args:
            model: 임베딩 모델명
                - jhgan/ko-sroberta-multitask (384차원, 한국어 특화, 추천)
                - paraphrase-multilingual-MiniLM-L12-v2 (384차원, 다국어)
                - intfloat/multilingual-e5-large (1024차원, 고성능 다국어)
        """
        self.model_name = model
        
        # M4 Pro MacBook의 GPU 활용 (MPS - Metal Performance Shaders)
        if torch.backends.mps.is_available():
            self.device = "mps"
            logger.info("✅ Apple Silicon GPU (MPS) 사용")
        elif torch.cuda.is_available():
            self.device = "cuda"
            logger.info("✅ CUDA GPU 사용")
        else:
            self.device = "cpu"
            logger.info("✅ CPU 사용")
        
        logger.info(f"임베딩 모델 로드 중: {model}")
        logger.info("⏳ 첫 실행 시 모델 다운로드 (약 100MB~500MB)...")
        
        # 모델 로드
        self.model = SentenceTransformer(model, device=self.device)
        
        # 차원 수 자동 감지
        self._dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"✅ EmbeddingClient 초기화 완료")
        logger.info(f"   - 모델: {self.model_name}")
        logger.info(f"   - 디바이스: {self.device}")
        logger.info(f"   - 임베딩 차원: {self._dimension}")
    
    def create_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트 (문자열 또는 문자열 리스트)
            
        Returns:
            임베딩 벡터 (단일 텍스트) 또는 벡터 리스트 (여러 텍스트)
        """
        try:
            # 입력이 리스트인지 단일 문자열인지 확인
            is_single = isinstance(text, str)
            texts = [text] if is_single else text
            
            # 빈 텍스트 필터링
            texts = [t.strip() for t in texts if t and t.strip()]
            
            if not texts:
                logger.warning("임베딩할 텍스트가 없습니다.")
                return [] if not is_single else []
            
            # 임베딩 생성 (배치 처리)
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=32
            )
            
            # numpy array를 리스트로 변환
            embeddings_list = embeddings.tolist()
            
            # 단일 텍스트인 경우 단일 벡터 반환
            if is_single:
                return embeddings_list[0]
            
            return embeddings_list
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            raise
    
    def create_query_embedding(self, query: str) -> List[float]:
        """
        검색 쿼리를 임베딩 벡터로 변환 (별칭 메서드)
        
        Args:
            query: 검색 쿼리
            
        Returns:
            임베딩 벡터
        """
        return self.create_embedding(query)
    
    def create_document_embeddings(self, documents: List[str]) -> List[List[float]]:
        """
        여러 문서를 한 번에 임베딩
        
        Args:
            documents: 문서 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        logger.info(f"📄 {len(documents)}개 문서 임베딩 생성 중...")
        embeddings = self.create_embedding(documents)
        logger.info(f"✅ 임베딩 생성 완료")
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        임베딩 차원 수 반환
        
        Returns:
            임베딩 벡터 차원 수
        """
        return self._dimension
    
    def test_connection(self) -> bool:
        """
        임베딩 시스템 테스트
        
        Returns:
            테스트 성공 여부
        """
        try:
            test_embedding = self.create_embedding("테스트")
            success = len(test_embedding) > 0 and len(test_embedding) == self._dimension
            if success:
                logger.info(f"✅ 임베딩 시스템 정상 작동 (차원: {self._dimension})")
            return success
        except Exception as e:
            logger.error(f"❌ 임베딩 시스템 테스트 실패: {str(e)}")
            return False
    
    def get_model_info(self) -> dict:
        """
        모델 정보 반환
        
        Returns:
            모델 정보 딕셔너리
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dimension": self._dimension,
            "is_gpu": self.device in ["cuda", "mps"],
            "model_type": "sentence-transformers (로컬)"
        }


# 한국어 특화 모델 추천
RECOMMENDED_KOREAN_MODELS = {
    "ko-sroberta-multitask": {
        "name": "jhgan/ko-sroberta-multitask",
        "dimension": 768,
        "description": "한국어 특화, 빠른 속도, 높은 정확도 (추천)",
        "size": "약 110MB"
    },
    "ko-sbert-multitask": {
        "name": "jhgan/ko-sbert-multitask",
        "dimension": 768,
        "description": "한국어 특화, 다양한 태스크 지원",
        "size": "약 110MB"
    },
    "multilingual-mini": {
        "name": "paraphrase-multilingual-MiniLM-L12-v2",
        "dimension": 384,
        "description": "다국어 지원, 작은 크기, 빠른 속도",
        "size": "약 120MB"
    },
    "multilingual-e5-large": {
        "name": "intfloat/multilingual-e5-large",
        "dimension": 1024,
        "description": "고성능 다국어 모델, 높은 정확도",
        "size": "약 560MB"
    }
}
