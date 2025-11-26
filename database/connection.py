"""
데이터베이스 연결 관리
"""
import psycopg2
import logging

from config.settings import DATABASE_URL, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)

def get_db_connection():
    """PostgreSQL 데이터베이스 연결 함수"""
    try:
        if DATABASE_URL and DATABASE_URL != "postgresql://username:password@localhost:5432/chat_history":
            return psycopg2.connect(DATABASE_URL)
        else:
            return psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
    except psycopg2.Error as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        raise

