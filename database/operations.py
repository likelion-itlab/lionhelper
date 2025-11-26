"""
데이터베이스 CRUD 작업
"""
import uuid
import logging
from typing import List

from database.connection import get_db_connection
from models.schemas import Session, Message

logger = logging.getLogger(__name__)

# ==================== 세션 관련 함수 ====================

def create_session(title: str = "새로운 대화") -> str:
    """새로운 채팅 세션 생성"""
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sessions (id, title) VALUES (%s, %s)
    ''', (session_id, title))
    
    conn.commit()
    conn.close()
    return session_id

def save_message(session_id: str, role: str, content: str, response_type: str = None, model_used: str = None) -> str:
    """메시지 저장"""
    message_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO messages (id, session_id, role, content, response_type, model_used)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (message_id, session_id, role, content, response_type, model_used))
    
    # 세션 업데이트 시간 갱신
    cursor.execute('''
        UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = %s
    ''', (session_id,))
    
    conn.commit()
    conn.close()
    return message_id

def get_sessions() -> List[Session]:
    """모든 세션 목록 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, created_at, updated_at 
        FROM sessions 
        ORDER BY updated_at DESC
    ''')
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append(Session(
            id=row[0],
            title=row[1],
            created_at=str(row[2]),
            updated_at=str(row[3])
        ))
    
    conn.close()
    return sessions

def get_session_messages(session_id: str) -> List[Message]:
    """특정 세션의 메시지 목록 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, session_id, role, content, response_type, model_used, created_at
        FROM messages 
        WHERE session_id = %s
        ORDER BY created_at ASC
    ''', (session_id,))
    
    messages = []
    for row in cursor.fetchall():
        messages.append(Message(
            id=row[0],
            session_id=row[1],
            role=row[2],
            content=row[3],
            response_type=row[4],
            model_used=row[5],
            created_at=str(row[6])
        ))
    
    conn.close()
    return messages

def delete_session(session_id: str):
    """세션과 관련 메시지 삭제"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM messages WHERE session_id = %s', (session_id,))
    cursor.execute('DELETE FROM sessions WHERE id = %s', (session_id,))
    
    conn.commit()
    conn.close()

def update_session_title(session_id: str, title: str):
    """세션 제목 업데이트"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE sessions SET title = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE id = %s
    ''', (title, session_id))
    
    conn.commit()
    conn.close()

