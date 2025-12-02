"""
RAG 기반 QA 검색 - Pinecone 벡터 검색 활용
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RAGSearchEngine:
    """RAG 기반 검색 엔진"""
    
    def __init__(self, embedding_client, pinecone_client):
        """
        RAG 검색 엔진 초기화
        
        Args:
            embedding_client: EmbeddingClient 인스턴스
            pinecone_client: PineconeClient 인스턴스
        """
        self.embedding_client = embedding_client
        self.pinecone_client = pinecone_client
        logger.info("RAGSearchEngine 초기화 완료")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.7,
        category_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        시맨틱 검색 수행
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 개수
            min_score: 최소 유사도 점수
            category_filter: 카테고리 필터 (선택사항)
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 쿼리 임베딩 생성
            query_vector = self.embedding_client.create_query_embedding(query)
            
            # 메타데이터 필터 구성
            filter_dict = None
            if category_filter:
                filter_dict = {"category": category_filter}
            
            # Pinecone 검색
            results = self.pinecone_client.query(
                query_vector=query_vector,
                top_k=top_k,
                filter_dict=filter_dict,
                include_metadata=True
            )
            
            # 결과 파싱 및 필터링
            parsed_results = []
            for result in results:
                score = result['score']
                
                # 최소 점수 이상만 포함
                if score >= min_score:
                    metadata = result.get('metadata', {})
                    
                    # 키워드 문자열을 리스트로 변환
                    keywords_str = metadata.get('keywords', '')
                    keywords_list = [k.strip() for k in keywords_str.split(',') if k.strip()]
                    
                    parsed_result = {
                        'id': result['id'],
                        'question': metadata.get('question', ''),
                        'answer': metadata.get('answer', ''),
                        'category': metadata.get('category', '기타'),
                        'keywords': keywords_list,
                        'matched_keywords': keywords_list,  # 호환성 유지
                        'score': round(score, 4),
                        'relevance_factors': ['semantic_search'],
                        'name': metadata.get('name', ''),
                        'source': metadata.get('source', '')
                    }
                    parsed_results.append(parsed_result)
            
            logger.info(f"검색 완료: {len(parsed_results)}개 결과 (최소 점수: {min_score})")
            return parsed_results
            
        except Exception as e:
            logger.error(f"검색 실패: {str(e)}")
            return []
    
    def search_by_keywords(
        self,
        keywords: List[str],
        top_k: int = 5,
        min_score: float = 0.6
    ) -> List[Dict]:
        """
        키워드 기반 검색 (여러 키워드를 결합하여 검색)
        
        Args:
            keywords: 키워드 리스트
            top_k: 반환할 결과 개수
            min_score: 최소 유사도 점수
            
        Returns:
            검색 결과 리스트
        """
        # 키워드를 자연어 쿼리로 변환
        query = ' '.join(keywords)
        return self.search(query, top_k=top_k, min_score=min_score)
    
    def get_related_questions(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.7
    ) -> List[Dict]:
        """
        관련 질문 검색 (기존 API 호환)
        
        Args:
            query: 검색 쿼리
            limit: 반환할 결과 개수
            min_score: 최소 유사도 점수
            
        Returns:
            관련 질문 리스트
        """
        return self.search(query, top_k=limit, min_score=min_score)


def find_related_questions_smart(
    query: str,
    limit: int = 5,
    min_score: float = 0.5,
    context_keywords: List[str] = None,
    rag_engine: Optional[RAGSearchEngine] = None
) -> List[Dict]:
    """
    지능적인 관련 질문 검색 (기존 함수와의 호환성 유지)
    
    Args:
        query: 검색 쿼리
        limit: 반환할 결과 개수
        min_score: 최소 점수
        context_keywords: 컨텍스트 키워드 (사용 안 함, 호환성 유지)
        rag_engine: RAGSearchEngine 인스턴스
        
    Returns:
        관련 질문 리스트
    """
    if not rag_engine:
        logger.warning("RAG 엔진이 제공되지 않았습니다. 빈 결과 반환")
        return []
    
    return rag_engine.search(query, top_k=limit, min_score=min_score)


def analyze_question_intent(user_input: str) -> Dict:
    """
    질문의 의도를 분석 (기존 함수 유지)
    
    Args:
        user_input: 사용자 입력
        
    Returns:
        의도 분석 결과
    """
    input_lower = user_input.lower().strip()
    
    # 일반적인 인사말/대화 패턴
    general_greetings = ["hi", "hello", "안녕", "헬로", "하이", "좋은아침", "안녕하세요", "반가워", "처음뵙겠습니다"]
    general_conversation = ["어떻게", "무엇", "뭐해", "잘지내", "기분", "날씨", "감사", "고마워", "미안", "죄송"]
    
    # 일반 대화 패턴 체크
    is_general_conversation = any(pattern in input_lower for pattern in 
                                general_greetings + general_conversation)
    
    # 질문 유형 분류
    intent_patterns = {
        "금액_문의": ["얼마", "금액", "돈", "원", "비용", "가격"],
        "시기_문의": ["언제", "몇일", "시간", "기간", "때", "일정"],
        "방법_문의": ["어떻게", "방법", "어디서", "누구", "절차", "과정"],
        "가능_여부": ["가능", "될까", "되나", "할 수 있", "괜찮", "상관없"],
        "조건_문의": ["조건", "요구사항", "필요", "기준", "자격"],
        "문제_해결": ["안돼", "안되", "오류", "문제", "고장", "실패", "불가"]
    }
    
    # 주제 카테고리 분류
    topic_categories = {
        "훈련장려금": ["훈련장려금", "장려금", "수당", "지급", "입금", "계좌"],
        "출결관리": ["출결", "출석", "지각", "조퇴", "외출", "결석", "QR"],
        "공결신청": ["공결", "병원", "진료", "입원", "예비군"],
        "교육도구": ["줌", "zoom", "노트북", "맥북", "교재"],
        "행정업무": ["서류", "증명서", "신청", "변경"],
        "수료_취업": ["수료", "취업", "인턴", "포트폴리오"],
    }
    
    # 타사 교육기관 키워드들
    competitor_keywords = [
        "스파르타", "코딩클럽", "코드스테이츠", "위코드", "패스트캠퍼스"
    ]
    
    detected_intent = "일반_문의"
    detected_topic = "기타"
    confidence = 0.0
    
    # 타사 교육기관 관련 질문인지 확인
    has_competitor_keywords = any(keyword in input_lower for keyword in competitor_keywords)
    is_competitor_question = has_competitor_keywords
    
    # 의도 분석
    for intent, keywords in intent_patterns.items():
        matches = sum(1 for keyword in keywords if keyword in input_lower)
        if matches > 0:
            detected_intent = intent
            confidence += matches * 0.2
            break
    
    # 주제 분석
    for topic, keywords in topic_categories.items():
        matches = sum(1 for keyword in keywords if keyword in input_lower)
        if matches > 0:
            detected_topic = topic
            confidence += matches * 0.3
            break
    
    return {
        "intent": detected_intent,
        "topic": detected_topic,
        "confidence": min(confidence, 1.0),
        "is_general_conversation": is_general_conversation,
        "is_competitor_question": is_competitor_question
    }

