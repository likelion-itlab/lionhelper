"""
라이언 헬퍼 AI 챗봇 메인 애플리케이션

기능별로 모듈화된 구조:
- config/: 설정 관리
- models/: Pydantic 스키마
- database/: 데이터베이스 연결 및 CRUD
- ai/: Claude 클라이언트 및 QA 검색
- services/: 비즈니스 로직
- auth/: 인증 처리
- api/: API 엔드포인트 (인라인으로 정의)
"""

import os
import time
import logging
from typing import Optional, List

from slack_sdk import WebClient

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

# 설정 import
from config.settings import (
    ANTHROPIC_API_KEY,
    SLACK_BOT_TOKEN,
    OLLAMA_MODEL
)

# 모델 import
from models.schemas import (
    ChatRequest, ChatResponse, RelatedQuestion,
    SessionCreate, Session, Message,
    SlackSyncRequest, SlackIssue,
    FeedbackRequest
)

# 데이터베이스 import
from database.init import init_database
from database.operations import (
    create_session, save_message, get_sessions,
    get_session_messages, delete_session, update_session_title
)

# AI 모듈 import
from ai.claude_client import ClaudeAPIClient
from ai.qa_data import QA_DATABASE
from ai.qa_search import (
    find_related_questions_smart,
    analyze_question_intent,
    find_best_match,
    get_context_keywords
)

# 서비스 import
from services.chat_service import call_claude_with_knowledge
from services.slack_service import sync_slack_issues, get_slack_issues
from services.feedback_service import (
    save_answer_feedback,
    analyze_feedback_patterns,
    get_improvement_suggestions_from_issues
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Claude 클라이언트 초기화
claude_client = None
if ANTHROPIC_API_KEY:
    try:
        claude_client = ClaudeAPIClient(ANTHROPIC_API_KEY)
        logger.info("Claude 클라이언트 초기화 완료")
    except Exception as e:
        logger.warning(f"Claude 클라이언트 초기화 실패: {str(e)}")

# 슬랙 클라이언트 초기화
slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None

# FastAPI 앱 초기화
app = FastAPI(
    title="라이언 헬퍼 AI 챗봇 & 검색 엔진 API",
    version="3.0.0",
    description="멋쟁이사자처럼 K-Digital Training 부트캠프 전문 AI 상담사"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400
)

# 추가 CORS 미들웨어
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response

# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"예상치 못한 오류: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"내부 서버 오류: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"요청 검증 오류: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={"detail": "요청 데이터가 유효하지 않습니다.", "errors": exc.errors()},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*"
        }
    )

# 정적 파일 서빙
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

# 앱 시작 시 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("데이터베이스 초기화 시작...")
        init_database()
        logger.info("데이터베이스 초기화 완료!")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        pass

print("🤖 Claude + 키워드 기반 지능형 AI 챗봇 시스템이 로드되었습니다.")
if claude_client:
    print("Claude-3-Haiku: 활성화됨")
else:
    print("Claude-3-Haiku: 비활성화됨 (API 키 확인 필요)")

# CORS preflight 요청을 위한 OPTIONS 핸들러
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    return JSONResponse(
        content="OK",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin",
            "Access-Control-Max-Age": "86400"
        }
    )

# ==================== API 엔드포인트 ====================

@app.get("/", tags=["Info"])
async def root():
    """메인 페이지"""
    try:
        return FileResponse("static/index.html")
    except:
        return {
            "message": "라이언 헬퍼 AI 챗봇 API (하이브리드 시스템)", 
            "status": "running",
            "model": f"Keyword-based + {OLLAMA_MODEL}",
            "language": "Korean"
        }

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_with_hybrid(request: ChatRequest):
    """Claude 지능형 AI 챗봇과 대화"""
    total_start_time = time.time()
    model_response_time_ms = None
    
    try:
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="메시지를 입력해주세요.")
        
        logger.info(f"사용자 질문: {request.prompt}")
        
        # Claude 지능형 응답 시스템
        if request.use_claude:
            logger.info("🧠 Claude 지능형 응답 시스템 시작")
            
            # 관련 키워드 정보 검색
            related_data = find_related_questions_smart(
                request.prompt, 
                limit=5,
                min_score=0.2,
                context_keywords=[]
            )
            
            # Claude가 키워드 정보를 참고해서 지능적 답변 생성
            try:
                ai_response, model_response_time_ms = await call_claude_with_knowledge(
                    claude_client,
                    request.prompt,
                    keyword_matches=related_data,
                    max_tokens=request.max_new_tokens,
                    session_id=request.session_id
                )
                
                if ai_response and len(ai_response.strip()) > 10:
                    # 관련 질문들 변환
                    related_questions = []
                    if related_data:
                        for rq in related_data[:4]:
                            related_questions.append(RelatedQuestion(
                                id=str(rq.get("id", "unknown")),
                                question=rq["question"],
                                answer_preview=rq["answer"][:100] + "...",
                                score=rq["score"],
                                matched_keywords=rq.get("matched_keywords", [])
                            ))
                    
                    # 대화 기록 저장
                    if request.session_id:
                        try:
                            save_message(request.session_id, "user", request.prompt)
                            save_message(request.session_id, "assistant", ai_response, 
                                       response_type="claude_enhanced", model_used="Claude-3-Haiku + Knowledge Base")
                        except Exception as e:
                            logger.warning(f"대화 기록 저장 실패: {str(e)}")
                    
                    total_response_time_ms = (time.time() - total_start_time) * 1000
                    
                    logger.info(f"✅ Claude 지능형 응답 생성 성공")
                    return ChatResponse(
                        response=ai_response,
                        model="Claude-3-Haiku + Knowledge Base",
                        status="success",
                        matched_keywords=[kw for item in related_data for kw in item.get("matched_keywords", [])][:5],
                        response_type="claude_enhanced",
                        related_questions=related_questions,
                        total_related=len(related_data),
                        response_time_ms=total_response_time_ms,
                        model_response_time_ms=model_response_time_ms
                    )
                    
            except Exception as e:
                logger.error(f"Claude 지능형 응답 실패: {str(e)}")
        
        # 키워드 기반 처리
        logger.info("키워드 기반 검색 모드 시작")
        
        # 질문 의도 분석
        user_intent = analyze_question_intent(request.prompt)
        logger.info(f"질문 의도 분석: {user_intent}")
        
        # 타사 정보 질문인 경우 제한 응답
        if user_intent.get("is_competitor_question", False):
            response = "죄송합니다. 저는 멋쟁이사자처럼 K-Digital Training 부트캠프와 관련된 질문만 답변드릴 수 있습니다."
            total_response_time_ms = (time.time() - total_start_time) * 1000
            return ChatResponse(
                response=response,
                model="Smart Intent-based Response System",
                status="competitor_question",
                matched_keywords=[],
                response_type="fallback",
                related_questions=None,
                total_related=0,
                response_time_ms=total_response_time_ms,
                model_response_time_ms=None
            )
        
        # 일반 대화인 경우 기본 응답
        if user_intent.get("is_general_conversation", False):
            user_input_lower = request.prompt.lower().strip()
            
            if any(greeting in user_input_lower for greeting in ["hi", "hello", "안녕", "하이", "헬로"]):
                response = "안녕하세요! 저는 멋쟁이사자처럼 K-Digital Training 부트캠프 전문 상담사입니다. 궁금한 점을 물어보세요!"
            elif any(word in user_input_lower for word in ["감사", "고마워", "고맙"]):
                response = "천만에요! 언제든지 궁금한 것이 있으시면 편하게 물어보세요."
            else:
                response = "안녕하세요! 무엇을 도와드릴까요? 훈련장려금, 출결, 공결 등 궁금한 점을 물어보세요."
            
            total_response_time_ms = (time.time() - total_start_time) * 1000
            return ChatResponse(
                response=response,
                model="Smart Intent-based Response System",
                status="greeting",
                matched_keywords=[],
                response_type="general_greeting",
                related_questions=None,
                total_related=0,
                response_time_ms=total_response_time_ms,
                model_response_time_ms=None
            )
        
        # 컨텍스트 키워드 추출
        context_keywords = get_context_keywords(request.session_id) if request.session_id else []
        
        # 키워드 기반 빠른 응답 시도
        best_match, score, matched_keywords = find_best_match(request.prompt)
        
        # 관련 질문들 검색
        related_questions_data = find_related_questions_smart(
            request.prompt, 
            limit=8,
            min_score=0.2,
            context_keywords=context_keywords
        )
        related_questions = []
        
        # 키워드 기반 답변 선택 로직
        response = "죄송합니다. 해당 질문에 대한 정확한 답변을 찾을 수 없습니다.\n\n구체적인 키워드(예: 훈련장려금, 출결, 줌 등)로 다시 질문해주시면 도움을 드릴 수 있습니다."
        status_val = "no_match"
        response_type = "fallback"
        model_name = "Smart Intent-based Response System"
        
        if related_questions_data and len(related_questions_data) > 0:
            best_question = related_questions_data[0]
            
            if best_question["score"] > 4.0:
                response = best_question["answer"]
                status_val = "success"
                response_type = "smart_keyword"
                matched_keywords = best_question["matched_keywords"]
                
                for rq in related_questions_data[1:]:
                    if rq["score"] > 1.5 and rq["id"] != best_question["id"]:
                        answer_preview = rq["answer"][:80] + "..." if len(rq["answer"]) > 80 else rq["answer"]
                        related_questions.append(RelatedQuestion(
                            id=rq["id"],
                            question=rq["question"],
                            answer_preview=answer_preview,
                            score=rq["score"],
                            matched_keywords=rq["matched_keywords"]
                        ))
            elif best_question["score"] > 1.0:
                response = best_question["answer"]
                status_val = "partial_match"
                response_type = "smart_keyword"
                matched_keywords = best_question["matched_keywords"]
        
        # 전체 응답 시간 계산
        total_response_time_ms = (time.time() - total_start_time) * 1000
        
        # 대화 기록 저장
        if request.session_id:
            try:
                save_message(request.session_id, "user", request.prompt)
                save_message(request.session_id, "assistant", response, response_type=response_type, model_used=model_name)
            except Exception as e:
                logger.warning(f"대화 기록 저장 실패: {str(e)}")
        
        return ChatResponse(
            response=response,
            model=model_name,
            status=status_val,
            matched_keywords=matched_keywords if matched_keywords else [],
            response_type=response_type,
            related_questions=related_questions[:4] if related_questions else None,
            total_related=len(related_questions) if related_questions else 0,
            response_time_ms=total_response_time_ms,
            model_response_time_ms=model_response_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"내부 서버 오류가 발생했습니다: {str(e)}")

@app.get("/health", tags=["Health"])
def health_check():
    """서버 상태 확인"""
    claude_status = "disconnected"
    if claude_client:
        try:
            test_result = claude_client.test_connection()
            claude_status = "connected" if test_result else "error"
        except:
            claude_status = "error"
    
    available_models = []
    if claude_status == "connected":
        available_models.append("Claude-3-Haiku")
    available_models.append("Keyword-based")
    
    return {
        "status": "healthy",
        "model": f"Intelligent: {' + '.join(available_models)}",
        "device": "CPU",
        "language": "Korean",
        "qa_count": len(QA_DATABASE),
        "claude_status": claude_status,
        "claude_available": bool(claude_client),
        "response_mode": "claude_enhanced_knowledge"
    }

@app.get("/info", tags=["Info"])
def get_info():
    """시스템 정보"""
    available_ai_models = []
    if claude_client:
        available_ai_models.append("Claude-3-Haiku")
    
    return {
        "model_name": f"Intelligent System: {' + '.join(available_ai_models) if available_ai_models else 'Keyword-based'}",
        "model_type": "Claude-Enhanced Knowledge System",
        "description": "Claude가 키워드 DB를 참고해서 지능적 답변을 생성하는 시스템",
        "qa_topics": list(QA_DATABASE.keys())
    }

@app.get("/search", tags=["Search"])
def search_questions(query: str, limit: Optional[int] = 10, min_score: Optional[float] = 0.1):
    """검색 엔진 - 관련 질문 검색"""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="검색어를 입력해주세요.")
    
    related_questions = find_related_questions_smart(query, limit=limit, min_score=min_score)
    
    search_results = []
    for rq in related_questions:
        answer_preview = rq["answer"][:100] + "..." if len(rq["answer"]) > 100 else rq["answer"]
        search_results.append({
            "id": rq["id"],
            "question": rq["question"],
            "answer": rq["answer"],
            "answer_preview": answer_preview,
            "keywords": rq.get("matched_keywords", []),
            "matched_keywords": rq.get("matched_keywords", []),
            "score": rq["score"],
            "match_type": "/".join(rq.get("relevance_factors", []))
        })
    
    return {
        "query": query,
        "total_found": len(search_results),
        "showing": len(search_results),
        "min_score": min_score,
        "results": search_results
    }

@app.get("/qa-list", tags=["QA"])
def get_qa_list(keyword: Optional[str] = None):
    """QA 목록 조회"""
    qa_list = []
    
    for qa_id, qa_data in QA_DATABASE.items():
        if keyword:
            keyword_lower = keyword.lower()
            if not any(keyword_lower in kw.lower() for kw in qa_data["keywords"]):
                continue
        
        qa_list.append({
            "id": qa_id,
            "question": qa_data["question"],
            "answer": qa_data["answer"],
            "keywords": qa_data["keywords"]
        })
    
    return {
        "total_count": len(qa_list),
        "keyword_filter": keyword,
        "qa_list": qa_list
    }

# ==================== 세션 관리 API ====================

@app.post("/sessions", response_model=Session, tags=["Sessions"])
def create_new_session(session_data: SessionCreate):
    """새 대화 세션 생성"""
    session_id = create_session(session_data.title)
    sessions = get_sessions()
    for session in sessions:
        if session.id == session_id:
            return session
    raise HTTPException(status_code=500, detail="세션 생성에 실패했습니다.")

@app.get("/sessions", response_model=List[Session], tags=["Sessions"])
def list_sessions():
    """대화 세션 목록 조회"""
    return get_sessions()

@app.get("/sessions/{session_id}/messages", response_model=List[Message], tags=["Sessions"])
def get_messages(session_id: str):
    """세션 메시지 조회"""
    messages = get_session_messages(session_id)
    if not messages:
        sessions = get_sessions()
        session_exists = any(s.id == session_id for s in sessions)
        if not session_exists:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return messages

@app.delete("/sessions/{session_id}", tags=["Sessions"])
def remove_session(session_id: str):
    """세션 삭제"""
    try:
        delete_session(session_id)
        return {"message": "세션이 삭제되었습니다.", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"세션 삭제 중 오류가 발생했습니다: {str(e)}")

@app.put("/sessions/{session_id}/title", tags=["Sessions"])
def rename_session(session_id: str, title_data: dict):
    """세션 제목 변경"""
    title = title_data.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="제목을 입력해주세요.")
    
    try:
        update_session_title(session_id, title)
        return {"message": "세션 제목이 변경되었습니다.", "session_id": session_id, "title": title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제목 변경 중 오류가 발생했습니다: {str(e)}")

@app.get("/sessions/{session_id}", response_model=Session, tags=["Sessions"])
def get_session_info(session_id: str):
    """세션 정보 조회"""
    sessions = get_sessions()
    for session in sessions:
        if session.id == session_id:
            return session
    raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

# ==================== 슬랙 API ====================

@app.post("/slack/sync", tags=["Slack"])
async def sync_slack_issues_endpoint(request: SlackSyncRequest):
    """슬랙 이슈 동기화"""
    if not SLACK_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="슬랙 봇 토큰이 설정되지 않았습니다.")
    
    result = await sync_slack_issues(slack_client, request.hours, request.force)
    return result

@app.get("/slack/issues", response_model=List[SlackIssue], tags=["Slack"])
def list_slack_issues_endpoint(limit: Optional[int] = 50, project: Optional[str] = None):
    """슬랙 이슈 목록 조회"""
    return get_slack_issues(limit=limit, project=project)

@app.get("/slack/issues/stats", tags=["Slack"])
def get_slack_issue_stats():
    """슬랙 이슈 통계"""
    from database.connection import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM slack_issues")
        total_issues = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT project, COUNT(*) as count 
            FROM slack_issues 
            GROUP BY project 
            ORDER BY count DESC
        """)
        by_project = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT issue_type, COUNT(*) as count 
            FROM slack_issues 
            GROUP BY issue_type 
            ORDER BY count DESC
        """)
        by_type = dict(cursor.fetchall())
        
        return {
            "total_issues": total_issues,
            "by_project": by_project,
            "by_type": by_type
        }
        
    finally:
        conn.close()

# ==================== 피드백 API ====================

@app.post("/feedback", tags=["Feedback"])
async def submit_feedback(request: FeedbackRequest):
    """답변 피드백 제출"""
    from database.connection import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content FROM messages 
            WHERE id = %s AND session_id = %s
        ''', (request.message_id, request.session_id))
        
        message_result = cursor.fetchone()
        if not message_result:
            conn.close()
            raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")
        
        ai_answer = message_result[0]
        
        cursor.execute('''
            SELECT content FROM messages 
            WHERE session_id = %s AND role = 'user'
            ORDER BY created_at DESC
            LIMIT 1
        ''', (request.session_id,))
        
        user_question_result = cursor.fetchone()
        user_question = user_question_result[0] if user_question_result else "질문을 찾을 수 없음"
        
        conn.close()
        
        success = save_answer_feedback(
            session_id=request.session_id,
            message_id=request.message_id,
            user_question=user_question,
            ai_answer=ai_answer,
            feedback_type=request.feedback_type,
            feedback_content=request.feedback_content,
            user_correction=request.user_correction
        )
        
        if success:
            return {"success": True, "message": "피드백이 성공적으로 저장되었습니다."}
        else:
            raise HTTPException(status_code=500, detail="피드백 저장에 실패했습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 처리 오류: {str(e)}")

@app.get("/feedback/analysis", tags=["Feedback"])
def get_feedback_analysis():
    """피드백 분석 결과"""
    try:
        analysis_result = analyze_feedback_patterns()
        return {"success": True, "data": analysis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 분석 오류: {str(e)}")

@app.get("/improvement/suggestions", tags=["Feedback"])
def get_improvement_suggestions():
    """답변 개선 제안"""
    try:
        issue_suggestions = get_improvement_suggestions_from_issues()
        feedback_analysis = analyze_feedback_patterns()
        
        priority_issues = [s for s in issue_suggestions if s.get("priority") == "high"]
        
        improvement_areas = {}
        for suggestion in issue_suggestions:
            area = suggestion.get("issue_type", "기타")
            if area not in improvement_areas:
                improvement_areas[area] = []
            improvement_areas[area].append(suggestion)
        
        return {
            "success": True,
            "data": {
                "suggestions": issue_suggestions,
                "priority_issues": priority_issues,
                "improvement_areas": improvement_areas,
                "feedback_analysis": feedback_analysis
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"개선 제안 생성 오류: {str(e)}")

# ==================== 서버 실행 ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    
    print("🚀 멋쟁이사자처럼 AI 챗봇 서버 시작!")
    print(f"📍 포트: {port}")
    print(f"🤖 Claude: {'✅ 연결됨' if claude_client else '❌ 연결 안됨'}")
    print(f"📚 QA 데이터베이스: {len(QA_DATABASE)}개 항목 로드됨")
    print("🌐 http://localhost:8001 에서 접속 가능합니다")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
