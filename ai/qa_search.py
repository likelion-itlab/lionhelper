"""
QA 검색 및 매칭 로직
"""
import logging
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

from ai.qa_data import QA_DATABASE
from database.operations import get_session_messages

logger = logging.getLogger(__name__)

def analyze_question_intent(user_input: str) -> dict:
    """질문의 의도를 분석하여 카테고리와 유형을 반환합니다."""
    input_lower = user_input.lower().strip()
    
    # 일반적인 인사말/대화 패턴
    general_greetings = ["hi", "hello", "안녕", "헬로", "하이", "좋은아침", "안녕하세요", "반가워", "처음뵙겠습니다"]
    general_conversation = ["어떻게", "무엇", "뭐해", "잘지내", "기분", "날씨", "감사", "고마워", "미안", "죄송"]
    code_questions = ["코드", "프로그래밍", "개발", "파이썬", "자바스크립트", "html", "css", "알고리즘", "함수", "변수"]
    general_questions = ["질문", "받아주", "도와주", "할 수 있", "가능한", "어떤", "무슨", "왜", "설명해"]
    
    # 일반 대화 패턴 체크
    is_general_conversation = any(pattern in input_lower for pattern in 
                                general_greetings + general_conversation + code_questions + general_questions)
    
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
        "훈련장려금": ["훈련장려금", "장려금", "수당", "지급", "입금", "계좌", "15800", "15,800"],
        "출결관리": ["출결", "출석", "지각", "조퇴", "외출", "결석", "QR", "체크", "입실", "퇴실", "HRD", "앱", "스크린샷"],
        "공결신청": ["공결", "병원", "진료", "입원", "예비군", "결혼", "상", "진단서", "처방전", "치과", "사랑니"],
        "교육도구": ["줌", "zoom", "노트북", "맥북", "교재", "캠", "배경", "설정", "화면", "웹캠", "카메라"],
        "행정업무": ["서류", "증명서", "신청", "변경", "계좌", "휴가", "실업급여", "수강증명서", "이사", "주소"],
        "수료_취업": ["수료", "취업", "인턴", "포트폴리오", "면접", "조기취업", "중도포기", "80%", "출석률"],
        "기초교육": ["기초클래스", "OT", "등록", "훈련생", "내일배움카드", "국취제", "국민취업지원제도"],
        "규정준수": ["해외여행", "해외출국", "장소이동", "개인소지", "화장실", "자리비움", "녹화본"]
    }
    
    # 타사 교육기관 키워드들
    competitor_keywords = [
        "스파르타", "코딩클럽", "코딩 클럽", "코드스테이츠", "코드스테이츠",
        "위코드", "wecode", "바닐라코딩", "바닐라 코딩", "패스트캠퍼스",
        "패스트 캠퍼스", "프로그래머스", "프로그래머스", "이노베이션",
        "부트캠프", "코딩학원", "코딩 학원", "it학원", "it 학원",
        "개발자교육", "개발자 교육", "프로그래밍학원", "프로그래밍 학원"
    ]
    
    # 자사 키워드
    company_keywords = [
        "멋쟁이사자처럼", "멋사", "kdt", "k-digital", "k digital"
    ]
    
    detected_intent = "일반_문의"
    detected_topic = "기타"
    confidence = 0.0
    
    # 타사 교육기관 관련 질문인지 확인
    has_competitor_keywords = any(keyword in input_lower for keyword in competitor_keywords)
    has_company_keywords = any(keyword in input_lower for keyword in company_keywords)
    is_competitor_question = has_competitor_keywords and not has_company_keywords
    
    # 일반 대화인 경우 특별 처리
    if is_general_conversation:
        detected_topic = "일반대화"
        confidence = 0.0
    elif is_competitor_question:
        detected_topic = "타사정보"
        confidence = 1.0
    else:
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
        "input_length": len(user_input),
        "question_words": len([w for w in input_lower.split() if w in ["뭐", "무엇", "어떤", "왜", "어디", "언제", "누구", "어떻게"]]),
        "is_general_conversation": is_general_conversation,
        "is_competitor_question": is_competitor_question
    }

def find_best_match(user_input: str) -> Tuple:
    """사용자 입력과 가장 잘 매칭되는 QA를 찾습니다."""
    user_input_lower = user_input.lower().strip()
    best_match = None
    best_score = 0
    matched_keywords = []
    
    for qa_id, qa_data in QA_DATABASE.items():
        score = 0
        keywords_found = []
        
        # 1. 정확한 키워드 매칭
        for keyword in qa_data["keywords"]:
            keyword_lower = keyword.lower()
            if keyword_lower in user_input_lower:
                score += 5
                keywords_found.append(keyword)
        
        # 2. 부분 키워드 매칭
        for keyword in qa_data["keywords"]:
            keyword_lower = keyword.lower()
            if len(keyword_lower) >= 2:
                user_words = user_input_lower.replace('?', '').replace('!', '').replace('.', '').split()
                for word in user_words:
                    if len(word) >= 2:
                        if (keyword_lower in word or word in keyword_lower) and keyword not in keywords_found:
                            score += 2
                            keywords_found.append(keyword)
        
        # 3. 질문 유사도
        question_similarity = SequenceMatcher(None, user_input_lower, qa_data["question"].lower()).ratio()
        if question_similarity > 0.3:
            score += question_similarity * 1
        
        # 4. 답변 내용 유사도
        answer_similarity = SequenceMatcher(None, user_input_lower, qa_data["answer"].lower()).ratio()
        if answer_similarity > 0.4:
            score += answer_similarity * 0.5
        
        if score > best_score:
            best_score = score
            best_match = qa_data
            matched_keywords = keywords_found
            
    return best_match, best_score, matched_keywords

def find_related_questions_smart(user_input: str, limit: int = 5, min_score: float = 0.5, context_keywords: List[str] = None) -> List[dict]:
    """지능적인 매칭 시스템으로 관련된 질문들을 점수순으로 반환합니다."""
    user_input_lower = user_input.lower().strip()
    related_questions = []
    
    # 질문 의도 분석
    intent_analysis = analyze_question_intent(user_input)
    logger.info(f"질문 의도 분석: {intent_analysis}")
    
    # 맥락 키워드가 있으면 추가 가중치 적용
    context_boost = {}
    if context_keywords:
        for keyword in context_keywords:
            context_boost[keyword.lower()] = 1.5
    
    for qa_id, qa_data in QA_DATABASE.items():
        score = 0
        keywords_found = []
        relevance_factors = []
        
        # 1. 의도 기반 매칭
        qa_intent = analyze_question_intent(qa_data["question"])
        if qa_intent["intent"] == intent_analysis["intent"] and qa_intent["topic"] == intent_analysis["topic"]:
            score += 10
            relevance_factors.append("intent_topic_match")
        elif qa_intent["intent"] == intent_analysis["intent"]:
            score += 6
            relevance_factors.append("intent_match")
        elif qa_intent["topic"] == intent_analysis["topic"]:
            score += 4
            relevance_factors.append("topic_match")
        
        # 2. 정확한 키워드 매칭
        for keyword in qa_data["keywords"]:
            keyword_lower = keyword.lower()
            if keyword_lower in user_input_lower:
                base_score = 3
                if keyword_lower in context_boost:
                    base_score *= context_boost[keyword_lower]
                score += base_score
                keywords_found.append(keyword)
                relevance_factors.append("exact_keyword")
        
        # 3. 의미론적 유사도
        question_similarity = SequenceMatcher(None, user_input_lower, qa_data["question"].lower()).ratio()
        if question_similarity > 0.4:
            score += question_similarity * 3
            relevance_factors.append("question_similarity")
        
        # 4. 답변 품질 점수
        answer_quality = min(len(qa_data["answer"]) / 100, 2.0)
        if any(word in qa_data["answer"] for word in ["예를 들어", "다만", "단,", "참고", "자세한"]):
            answer_quality += 0.5
        score += answer_quality
        
        # 5. 부분 키워드 매칭
        for keyword in qa_data["keywords"]:
            keyword_lower = keyword.lower()
            if len(keyword_lower) >= 2:
                user_words = user_input_lower.replace('?', '').replace('!', '').replace('.', '').split()
                for word in user_words:
                    if len(word) >= 2:
                        if (keyword_lower in word or word in keyword_lower) and keyword not in keywords_found:
                            base_score = 1
                            if keyword_lower in context_boost:
                                base_score *= context_boost[keyword_lower]
                            score += base_score
                            keywords_found.append(keyword)
                            relevance_factors.append("partial_keyword")
        
        # 최소 점수 이상인 경우만 포함
        if score >= min_score:
            related_questions.append({
                "id": qa_id,
                "question": qa_data["question"],
                "answer": qa_data["answer"],
                "score": round(score, 2),
                "matched_keywords": keywords_found,
                "relevance_factors": relevance_factors,
                "intent": qa_intent["intent"],
                "topic": qa_intent["topic"]
            })
    
    # 점수순으로 정렬하고 제한된 개수만 반환
    related_questions.sort(key=lambda x: x["score"], reverse=True)
    return related_questions[:limit]

def get_context_keywords(session_id: str) -> List[str]:
    """세션의 이전 대화에서 자주 나온 키워드들을 추출합니다."""
    if not session_id:
        return []
    
    try:
        messages = get_session_messages(session_id)
        keyword_count = {}
        
        # 최근 5개 메시지만 분석
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        for message in recent_messages:
            if message.role == "user":
                content_lower = message.content.lower()
                
                # QA 데이터베이스의 모든 키워드와 매칭
                for qa_id, qa_data in QA_DATABASE.items():
                    for keyword in qa_data["keywords"]:
                        keyword_lower = keyword.lower()
                        if keyword_lower in content_lower:
                            keyword_count[keyword_lower] = keyword_count.get(keyword_lower, 0) + 1
        
        # 빈도순으로 정렬하여 상위 키워드 반환
        sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:5]]
        
    except Exception as e:
        logger.warning(f"컨텍스트 키워드 추출 실패: {str(e)}")
        return []

def get_conversation_context(session_id: str, max_messages: int = 6) -> str:
    """세션의 최근 대화 내용을 컨텍스트로 반환합니다."""
    if not session_id:
        return ""
    
    try:
        messages = get_session_messages(session_id)
        if not messages:
            return ""
        
        # 최근 대화만 가져오기
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        context_parts = []
        for message in recent_messages:
            role_name = "사용자" if message.role == "user" else "상담사"
            context_parts.append(f"{role_name}: {message.content}")
        
        if context_parts:
            return "\n".join(context_parts)
        return ""
        
    except Exception as e:
        logger.warning(f"대화 컨텍스트 추출 실패: {str(e)}")
        return ""

def get_conversation_summary(session_id: str) -> str:
    """세션의 대화 주제와 맥락을 요약합니다."""
    if not session_id:
        return ""
    
    try:
        messages = get_session_messages(session_id)
        if not messages or len(messages) < 2:
            return ""
        
        # 사용자 메시지들만 추출하여 주제 파악
        user_messages = [msg.content for msg in messages if msg.role == "user"]
        if not user_messages:
            return ""
        
        # 최근 3개 사용자 메시지로 주제 파악
        recent_topics = user_messages[-3:] if len(user_messages) >= 3 else user_messages
        
        # 간단한 주제 키워드 추출
        topic_keywords = []
        for message in recent_topics:
            content_lower = message.lower()
            if any(word in content_lower for word in ["훈련장려금", "장려금", "지급"]):
                topic_keywords.append("훈련장려금")
            if any(word in content_lower for word in ["출결", "출석", "지각", "조퇴"]):
                topic_keywords.append("출결관리")
            if any(word in content_lower for word in ["공결", "결석", "병가"]):
                topic_keywords.append("공결신청")
            if any(word in content_lower for word in ["줌", "온라인", "수업"]):
                topic_keywords.append("온라인수업")
            if any(word in content_lower for word in ["노트북", "대여", "기기"]):
                topic_keywords.append("노트북대여")
        
        # 중복 제거하고 주제 요약
        unique_topics = list(set(topic_keywords))
        if unique_topics:
            return f"이전 대화 주제: {', '.join(unique_topics)}"
        return ""
        
    except Exception as e:
        logger.warning(f"대화 요약 생성 실패: {str(e)}")
        return ""

def get_conversation_flow(session_id: str) -> str:
    """대화의 흐름과 맥락을 파악합니다."""
    if not session_id:
        return ""
    
    try:
        messages = get_session_messages(session_id)
        if not messages or len(messages) < 4:
            return ""
        
        # 최근 대화 흐름 분석
        recent_messages = messages[-6:] if len(messages) > 6 else messages
        
        flow_indicators = []
        
        # 질문 패턴 분석
        for i, message in enumerate(recent_messages):
            if message.role == "user":
                content_lower = message.content.lower()
                
                # 연속 질문 패턴
                if any(word in content_lower for word in ["그러면", "그럼", "그래서", "그렇다면"]):
                    flow_indicators.append("연속 질문")
                
                # 구체화 질문 패턴
                if any(word in content_lower for word in ["몇", "얼마", "언제", "어떻게", "왜"]):
                    flow_indicators.append("구체적 질문")
                
                # 확인 질문 패턴
                if any(word in content_lower for word in ["괜찮", "가능", "되나", "할 수 있"]):
                    flow_indicators.append("확인 질문")
        
        if flow_indicators:
            return f"대화 흐름: {', '.join(set(flow_indicators))}"
        return ""
        
    except Exception as e:
        logger.warning(f"대화 흐름 분석 실패: {str(e)}")
        return ""

def get_user_context(session_id: str) -> str:
    """사용자의 상황과 맥락을 파악합니다."""
    if not session_id:
        return ""
    
    try:
        messages = get_session_messages(session_id)
        if not messages:
            return ""
        
        # 사용자 메시지에서 상황 파악
        user_messages = [msg.content for msg in messages if msg.role == "user"]
        if not user_messages:
            return ""
        
        context_indicators = []
        
        for message in user_messages:
            content_lower = message.lower()
            
            # 긴급성 표현
            if any(word in content_lower for word in ["급해", "빨리", "어떻게 해야", "도와줘"]):
                context_indicators.append("긴급 상황")
            
            # 불안감 표현
            if any(word in content_lower for word in ["걱정", "불안", "어떻게 될까", "괜찮을까"]):
                context_indicators.append("불안감")
            
            # 구체적 상황
            if any(word in content_lower for word in ["몇 일", "몇 번", "몇 개", "얼마나"]):
                context_indicators.append("구체적 상황")
        
        if context_indicators:
            return f"사용자 상황: {', '.join(set(context_indicators))}"
        return ""
        
    except Exception as e:
        logger.warning(f"사용자 맥락 분석 실패: {str(e)}")
        return ""

def get_conversation_memory(session_id: str) -> str:
    """대화에서 언급된 구체적인 정보들을 기억합니다."""
    if not session_id:
        return ""
    
    try:
        messages = get_session_messages(session_id)
        if not messages:
            return ""
        
        memory_items = []
        
        # 최근 대화에서 구체적인 정보 추출
        recent_messages = messages[-8:] if len(messages) > 8 else messages
        
        for message in recent_messages:
            if message.role == "user":
                content = message.content
                
                # 숫자 정보 추출
                import re
                numbers = re.findall(r'\d+', content)
                if numbers:
                    for num in numbers:
                        if any(word in content.lower() for word in ["일", "번", "개", "회"]):
                            memory_items.append(f"사용자가 언급한 숫자: {num}")
                
                # 구체적인 상황 추출
                if "16일" in content:
                    memory_items.append("16일 출석 관련 질문")
                if "80%" in content:
                    memory_items.append("80% 출석률 관련 질문")
                if "공결" in content:
                    memory_items.append("공결 관련 질문")
                if "훈련장려금" in content:
                    memory_items.append("훈련장려금 관련 질문")
        
        if memory_items:
            return f"대화 기억: {', '.join(set(memory_items))}"
        return ""
        
    except Exception as e:
        logger.warning(f"대화 기억 분석 실패: {str(e)}")
        return ""

