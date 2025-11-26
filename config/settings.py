"""
애플리케이션 설정 및 환경 변수 관리
"""
import os

# JWT 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Google OAuth 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your-google-client-secret")

# 슬랙 API 설정
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = "C08M47TM2KH"

# Anthropic Claude API 설정
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
USE_CLAUDE = os.getenv("USE_CLAUDE", "true").lower() == "true"

# Ollama 설정 (백업용)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "GPT-OSS-20B")

# PostgreSQL 데이터베이스 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/chat_history")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "chat_history")
DB_USER = os.getenv("DB_USER", "username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

