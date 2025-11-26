# 멀티 플랫폼 지원 (맥 M1/M2/M3 + 인텔/윈도우)
FROM --platform=$BUILDPLATFORM python:3.11-slim

# 빌드 인자
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# 메타데이터
LABEL maintainer="helper-team"
LABEL description="라이언 헬퍼 AI 챗봇 - Claude + 키워드 기반 시스템"

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 시스템 패키지 설치 (PostgreSQL 클라이언트 포함)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 먼저 복사 및 설치 (캐싱 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사 (모듈화된 구조)
COPY config/ ./config/
COPY models/ ./models/
COPY database/ ./database/
COPY ai/ ./ai/
COPY services/ ./services/
COPY auth/ ./auth/
COPY api/ ./api/
COPY static/ ./static/
COPY main.py .

# 포트 노출
EXPOSE 8001

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 비루트 사용자로 실행 (보안)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 애플리케이션 실행
CMD ["python", "main.py"]

