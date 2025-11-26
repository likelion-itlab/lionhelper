"""
채팅 서비스 - Claude와 키워드 기반 응답 처리
"""
import time
import logging
from typing import Optional, List, Dict, Tuple

from ai.claude_client import ClaudeAPIClient
from ai.qa_search import (
    find_related_questions_smart,
    get_conversation_context,
    get_conversation_summary,
    get_conversation_flow,
    get_user_context,
    get_conversation_memory
)

logger = logging.getLogger(__name__)

async def call_claude_with_knowledge(
    claude_client: ClaudeAPIClient,
    user_prompt: str, 
    keyword_matches: List[dict] = None, 
    max_tokens: int = 1000, 
    session_id: str = None
) -> Tuple[Optional[str], Optional[float]]:
    """Claude가 키워드 DB 정보와 대화 컨텍스트를 참고해서 지능적인 답변을 생성
    
    Returns:
        tuple[Optional[str], Optional[float]]: (응답 텍스트, 응답 시간(ms))
    """
    if not claude_client:
        logger.warning("Claude 클라이언트가 초기화되지 않았습니다")
        return None, None
    
    try:
        # Claude API 호출 시간 측정 시작
        model_start_time = time.time()
        
        # 대화 컨텍스트 가져오기
        conversation_context = ""
        conversation_summary = ""
        conversation_flow = ""
        user_context = ""
        conversation_memory = ""
        
        if session_id:
            conversation_context = get_conversation_context(session_id)
            conversation_summary = get_conversation_summary(session_id)
            conversation_flow = get_conversation_flow(session_id)
            user_context = get_user_context(session_id)
            conversation_memory = get_conversation_memory(session_id)
        
        # 훈련 전문가로서의 시스템 컨텍스트
        system_context = """멋쟁이사자처럼 K-Digital Training 부트캠프 전문 AI 상담사입니다.

역할: 훈련생 질문에 정확하고 친절하게 답변, 규정/절차 명확 안내

전문분야: 훈련장려금(일일 15,800원, 80% 출석), 출결관리(QR체크, HRD앱), 공결신청, 온라인수업(줌), 노트북 대여, 수료조건

⚠️ 멋쟁이사자처럼 부트캠프 관련 정보만 제공. 타 기관 질문 시 정중히 거절."""

        # 대화 컨텍스트가 있는 경우 추가
        context_section = ""
        if conversation_context:
            context_section = f"""

💬 이전 대화: {conversation_context}
{conversation_summary}{conversation_flow}{user_context}{conversation_memory}
위 내용 참고하여 연속성 있게 답변."""

        if keyword_matches and len(keyword_matches) > 0:
            # 키워드 매칭된 정보들을 참고 자료로 활용
            reference_info = "\n\n📚 참고:\n"
            for i, match in enumerate(keyword_matches[:2], 1):
                reference_info += f"{i}. Q: {match['question']}\n"
                reference_info += f"   A: {match['answer'][:100]}{'...' if len(match['answer']) > 100 else ''}\n\n"
            
            enhanced_prompt = f"""{system_context}{context_section}

{reference_info}위 참고 정보를 바탕으로 다음 질문에 정확하고 자연스럽게 답변해주세요:

질문: {user_prompt}

답변 가이드: 참고 정보 기반 자연스러운 설명, 이전 대화 맥락 유지, 친근하고 전문적인 톤, 단계별 설명. 타사 질문은 정중히 거절."""
        else:
            # 키워드 매칭이 없는 경우 일반 대화
            enhanced_prompt = f"""{system_context}{context_section}

다음 질문에 멋쟁이사자처럼 부트캠프 상담사로서 답변해주세요:

질문: {user_prompt}

답변 가이드: 친근하고 도움되는 톤, 이전 대화 맥락 유지, 부트캠프 관련 정보 제공. 타사 질문은 정중히 거절."""
        
        # Claude API 호출
        response = claude_client.make_request(enhanced_prompt, max_tokens)
        
        # Claude API 호출 시간 측정 종료
        model_end_time = time.time()
        model_response_time_ms = (model_end_time - model_start_time) * 1000
        
        if response:
            logger.info(f"Claude 지식 기반 응답 생성 성공 (응답 시간: {model_response_time_ms:.2f}ms)")
            return response.strip(), model_response_time_ms
        else:
            logger.warning("Claude 지식 기반 응답이 비어있습니다")
            return None, model_response_time_ms
            
    except Exception as e:
        logger.error(f"Claude 지식 기반 응답 실패: {str(e)}")
        return None, None

