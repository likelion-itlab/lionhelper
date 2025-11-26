"""
데이터베이스 초기화
"""
import psycopg2
import logging

from database.connection import get_db_connection

logger = logging.getLogger(__name__)

def init_database():
    """PostgreSQL 데이터베이스 초기화"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 세션 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(255) PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 메시지 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id VARCHAR(255) PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                response_type VARCHAR(100),
                model_used VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        
        # 사용자 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                picture TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 슬랙 이슈 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slack_issues (
                id VARCHAR(255) PRIMARY KEY,
                project VARCHAR(255) NOT NULL,
                issue_type VARCHAR(100) NOT NULL,
                author VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                channel_id VARCHAR(255),
                timestamp VARCHAR(255),
                slack_ts VARCHAR(255) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
        # 답변 피드백 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS answer_feedback (
                id VARCHAR(255) PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                message_id VARCHAR(255) NOT NULL,
                user_question TEXT NOT NULL,
                ai_answer TEXT NOT NULL,
                feedback_type VARCHAR(50) NOT NULL,
                feedback_content TEXT,
                user_correction TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (message_id) REFERENCES messages (id)
            )
        ''')
        
        # 답변 개선 로그 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvement_logs (
                id VARCHAR(255) PRIMARY KEY,
                issue_type VARCHAR(100) NOT NULL,
                original_answer TEXT NOT NULL,
                improved_answer TEXT NOT NULL,
                improvement_reason TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.info("PostgreSQL 데이터베이스 초기화 완료")
        
    except psycopg2.Error as e:
        logger.error(f"데이터베이스 초기화 오류: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

