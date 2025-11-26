"""
피드백 시스템 서비스
"""
import uuid
import logging
from typing import Dict, Any, List

from database.connection import get_db_connection

logger = logging.getLogger(__name__)

def save_answer_feedback(
    session_id: str, 
    message_id: str, 
    user_question: str, 
    ai_answer: str, 
    feedback_type: str, 
    feedback_content: str = None, 
    user_correction: str = None
) -> bool:
    """답변 피드백을 데이터베이스에 저장합니다."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        feedback_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO answer_feedback 
            (id, session_id, message_id, user_question, ai_answer, feedback_type, feedback_content, user_correction)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (feedback_id, session_id, message_id, user_question, ai_answer, feedback_type, feedback_content, user_correction))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"피드백 저장 오류: {e}")
        return False

def analyze_feedback_patterns() -> Dict[str, Any]:
    """피드백 패턴을 분석하여 개선점을 찾습니다."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 부정적 피드백이 많은 질문 유형 분석
        cursor.execute('''
            SELECT user_question, COUNT(*) as negative_count
            FROM answer_feedback 
            WHERE feedback_type = 'negative'
            GROUP BY user_question
            ORDER BY negative_count DESC
            LIMIT 10
        ''')
        problematic_questions = cursor.fetchall()
        
        # 자주 수정되는 답변 패턴 분석
        cursor.execute('''
            SELECT user_correction, COUNT(*) as correction_count
            FROM answer_feedback 
            WHERE feedback_type = 'correction' AND user_correction IS NOT NULL
            GROUP BY user_correction
            ORDER BY correction_count DESC
            LIMIT 10
        ''')
        common_corrections = cursor.fetchall()
        
        # 전체 피드백 통계
        cursor.execute('''
            SELECT feedback_type, COUNT(*) as count
            FROM answer_feedback
            GROUP BY feedback_type
        ''')
        feedback_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            "problematic_questions": [{"question": q[0], "count": q[1]} for q in problematic_questions],
            "common_corrections": [{"correction": c[0], "count": c[1]} for c in common_corrections],
            "feedback_stats": [{"type": f[0], "count": f[1]} for f in feedback_stats]
        }
    except Exception as e:
        logger.error(f"피드백 분석 오류: {e}")
        return {}

def get_improvement_suggestions_from_issues() -> List[Dict[str, str]]:
    """슬랙 이슈 데이터를 기반으로 답변 개선 제안을 생성합니다."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 최근 이슈들 가져오기
        cursor.execute('''
            SELECT project, issue_type, content, author
            FROM slack_issues
            ORDER BY created_at DESC
            LIMIT 20
        ''')
        recent_issues = cursor.fetchall()
        
        suggestions = []
        for issue in recent_issues:
            project, issue_type, content, author = issue
            
            # 이슈 유형별 개선 제안 생성
            if "정확도" in content or "틀린" in content or "잘못" in content:
                suggestions.append({
                    "issue_type": "답변 정확도",
                    "description": f"{project}에서 {issue_type} 관련 정확도 문제 발생",
                    "suggestion": "해당 분야의 QA 데이터베이스 업데이트 및 검증 강화 필요",
                    "priority": "high"
                })
            elif "느린" in content or "속도" in content:
                suggestions.append({
                    "issue_type": "응답 속도",
                    "description": f"{project}에서 응답 속도 문제 발생",
                    "suggestion": "캐싱 시스템 개선 및 응답 최적화 필요",
                    "priority": "medium"
                })
        
        conn.close()
        return suggestions
    except Exception as e:
        logger.error(f"개선 제안 생성 오류: {e}")
        return []

