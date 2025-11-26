# 🐳 Docker 사용 가이드

## ✅ 멀티 플랫폼 지원

이 프로젝트는 **맥(M1/M2/M3 ARM64 + 인텔 x86_64)**과 **윈도우(x86_64)** 모두에서 동일하게 작동합니다!

## 📋 사전 준비

### 1. Docker 설치
- **맥**: [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- **윈도우**: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

### 2. 환경 변수 설정
```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 열어서 API 키 입력
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
# SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx
# SECRET_KEY=your-super-secret-key-min-32-characters
```

## 🚀 실행 방법

### 방법 1: Docker Compose 사용 (권장)

#### 맥/리눅스
```bash
# 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f app

# 중지
docker-compose down

# 완전 삭제 (볼륨 포함)
docker-compose down -v
```

#### 윈도우 (PowerShell)
```powershell
# 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f app

# 중지
docker-compose down
```

### 방법 2: Docker 직접 사용

#### 멀티 플랫폼 빌드 (권장)
```bash
# buildx 활성화 (한 번만 실행)
docker buildx create --use

# 맥(ARM64)과 윈도우(x86_64) 모두 지원하는 이미지 빌드
docker buildx build --platform linux/amd64,linux/arm64 -t helper-app:latest --load .
```

#### 단일 플랫폼 빌드
```bash
# x86_64 (윈도우, 인텔맥)
docker build --platform linux/amd64 -t helper-app:latest .

# ARM64 (애플 실리콘 맥)
docker build --platform linux/arm64 -t helper-app:latest .

# 현재 플랫폼 자동 감지
docker build -t helper-app:latest .
```

#### 실행
```bash
# 맥/리눅스
docker run -d \
  --name helper-app \
  -p 8001:8001 \
  -e ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxx" \
  -e SECRET_KEY="your-secret-key" \
  helper-app:latest

# 윈도우 (PowerShell)
docker run -d `
  --name helper-app `
  -p 8001:8001 `
  -e ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxx" `
  -e SECRET_KEY="your-secret-key" `
  helper-app:latest
```

## 🔍 테스트

### 헬스체크
```bash
# 맥/리눅스
curl http://localhost:8001/health

# 윈도우 (PowerShell)
Invoke-WebRequest -Uri http://localhost:8001/health
```

### API 테스트
```bash
# 채팅 테스트
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "훈련장려금은 얼마인가요?", "use_claude": true}'

# 검색 테스트
curl "http://localhost:8001/search?query=훈련장려금&limit=5"
```

## 🔧 트러블슈팅

### 1. 플랫폼 이슈
```bash
# 현재 플랫폼 확인
docker version | grep -i "os/arch"

# 강제로 플랫폼 지정
docker build --platform linux/amd64 -t helper-app .
```

### 2. 네트워크 이슈 (윈도우)
```powershell
# Docker Desktop 재시작
# 또는 WSL2 업데이트
wsl --update
```

### 3. 볼륨 권한 이슈
```bash
# 맥/리눅스
chmod -R 755 ./logs

# 윈도우에서는 대부분 자동 처리
```

### 4. 메모리 이슈
```bash
# Docker Desktop > Settings > Resources에서 메모리 증가
# 권장: 최소 4GB
```

## 📊 플랫폼별 차이점

### 동일한 것
✅ 애플리케이션 동작  
✅ API 응답  
✅ 데이터베이스 스키마  
✅ 환경 변수  
✅ 네트워크 설정  

### 주의할 것
⚠️ 파일 경로 구분자 (/ vs \)  
⚠️ 줄바꿈 문자 (LF vs CRLF)  
⚠️ CPU 아키텍처 (ARM64 vs x86_64)  

## 🎯 최적화 팁

### 빌드 속도 향상
```bash
# BuildKit 활성화
export DOCKER_BUILDKIT=1

# 빌드 캐시 활용
docker build --cache-from helper-app:latest -t helper-app:latest .
```

### 이미지 크기 최적화
```bash
# 현재 이미지 크기 확인
docker images helper-app

# 불필요한 이미지 정리
docker image prune -a
```

### 멀티 스테이지 빌드 (선택사항)
더 작은 이미지를 원하면 Dockerfile에 멀티 스테이지 빌드를 추가할 수 있습니다.

## 🌍 배포

### Docker Hub에 푸시
```bash
# 태그 생성
docker tag helper-app:latest yourusername/helper-app:latest

# 푸시
docker push yourusername/helper-app:latest

# 다운로드 (다른 환경에서)
docker pull yourusername/helper-app:latest
```

### 여러 플랫폼 이미지 푸시
```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourusername/helper-app:latest \
  --push .
```

## 💡 결론

**맥에서 테스트한 Docker 이미지는 윈도우에서도 100% 동일하게 작동합니다!**

단, 멀티 플랫폼 빌드를 사용하면 더욱 호환성이 좋습니다:

```bash
# 이 명령어 하나면 맥과 윈도우 모두 지원
docker buildx build --platform linux/amd64,linux/arm64 -t helper-app:latest --load .
```

---
**참고**: Docker Compose를 사용하면 플랫폼 차이를 신경 쓸 필요가 없습니다!

