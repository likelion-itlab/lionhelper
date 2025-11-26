"""
Pydantic 모델 정의
"""
from typing import Optional, List
from pydantic import BaseModel, Field

# ==================== 채팅 관련 모델 ====================

class RelatedQuestion(BaseModel):
    """관련 질문 모델"""
    id: str = Field(..., description="질문 고유 ID")
    question: str = Field(..., description="관련 질문")
    answer_preview: str = Field(..., description="답변 미리보기")
    score: float = Field(..., description="관련도 점수")
    matched_keywords: List[str] = Field(..., description="매칭된 키워드")

class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    prompt: str = Field(..., description="사용자 질문 또는 메시지", example="안녕? 훈련장려금 언제 받을 수 있어?")
    max_new_tokens: Optional[int] = Field(600, description="Claude 응답 최대 토큰 수", example=600, ge=50, le=2048)
    temperature: Optional[float] = Field(0.7, description="Claude 창의성 조절", example=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(0.9, description="확률 임계값", example=0.9, ge=0.0, le=1.0)
    use_claude: Optional[bool] = Field(True, description="Claude 사용 여부", example=True)
    session_id: Optional[str] = Field(None, description="대화 세션 ID", example="claude-chat-001")

class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    response: str = Field(..., description="응답 메시지")
    model: str = Field(..., description="사용된 모델")
    status: str = Field(..., description="응답 상태")
    matched_keywords: Optional[List[str]] = Field(None, description="매칭된 키워드")
    response_type: str = Field(..., description="응답 유형")
    related_questions: Optional[List[RelatedQuestion]] = Field(None, description="관련 질문 목록")
    total_related: Optional[int] = Field(None, description="관련 질문 총 개수")
    response_time_ms: Optional[float] = Field(None, description="응답 생성 시간(ms)")
    model_response_time_ms: Optional[float] = Field(None, description="AI 모델 응답 시간(ms)")

# ==================== 세션 관련 모델 ====================

class SessionCreate(BaseModel):
    """새 세션 생성 요청 모델"""
    title: Optional[str] = Field("새로운 대화", description="세션 제목", example="훈련장려금 문의")

class Session(BaseModel):
    """세션 정보 모델"""
    id: str = Field(..., description="세션 고유 ID")
    title: str = Field(..., description="세션 제목")
    created_at: str = Field(..., description="생성 시간")
    updated_at: str = Field(..., description="최종 업데이트 시간")

class Message(BaseModel):
    """메시지 모델"""
    id: str = Field(..., description="메시지 고유 ID")
    session_id: str = Field(..., description="세션 ID")
    role: str = Field(..., description="발신자 (user/assistant)")
    content: str = Field(..., description="메시지 내용")
    response_type: Optional[str] = Field(None, description="응답 유형")
    model_used: Optional[str] = Field(None, description="사용된 모델명")
    created_at: str = Field(..., description="생성 시간")

# ==================== 사용자 인증 관련 모델 ====================

class User(BaseModel):
    """사용자 정보 모델"""
    id: str = Field(..., description="사용자 고유 ID")
    email: str = Field(..., description="이메일 주소")
    name: str = Field(..., description="사용자 이름")
    picture: Optional[str] = Field(None, description="프로필 사진 URL")
    created_at: str = Field(..., description="계정 생성일")

class Token(BaseModel):
    """토큰 응답 모델"""
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(..., description="토큰 타입", example="bearer")
    expires_in: int = Field(..., description="토큰 만료 시간(초)", example=1800)
    user: User = Field(..., description="사용자 정보")

class LoginResponse(BaseModel):
    """로그인 응답 모델"""
    success: bool = Field(..., description="로그인 성공 여부")
    message: str = Field(..., description="응답 메시지")
    token: Optional[Token] = Field(None, description="토큰 정보")
    user: Optional[User] = Field(None, description="사용자 정보")

# ==================== 슬랙 관련 모델 ====================

class SlackIssue(BaseModel):
    """슬랙 이슈 모델"""
    id: str = Field(..., description="이슈 고유 ID")
    project: str = Field(..., description="프로젝트/과정명")
    issue_type: str = Field(..., description="이슈 유형")
    author: str = Field(..., description="작성자")
    content: str = Field(..., description="이슈 내용")
    raw_message: str = Field(..., description="원본 메시지")
    channel_id: Optional[str] = Field(None, description="채널 ID")
    timestamp: Optional[str] = Field(None, description="타임스탬프")
    slack_ts: Optional[str] = Field(None, description="슬랙 타임스탬프")
    created_at: str = Field(..., description="생성 시간")

class SlackSyncRequest(BaseModel):
    """슬랙 동기화 요청 모델"""
    hours: Optional[int] = Field(24, description="동기화할 시간 범위 (시간)", example=24)
    force: Optional[bool] = Field(False, description="강제 동기화 여부", example=False)

# ==================== 피드백 관련 모델 ====================

class FeedbackRequest(BaseModel):
    """답변 피드백 요청 모델"""
    session_id: str = Field(..., description="세션 ID")
    message_id: str = Field(..., description="메시지 ID")
    feedback_type: str = Field(..., description="피드백 유형", example="negative")
    feedback_content: Optional[str] = Field(None, description="피드백 내용")
    user_correction: Optional[str] = Field(None, description="사용자 수정 내용")

class ImprovementSuggestion(BaseModel):
    """답변 개선 제안 모델"""
    issue_type: str = Field(..., description="이슈 유형")
    current_answer: str = Field(..., description="현재 답변")
    suggested_answer: str = Field(..., description="개선된 답변")
    improvement_reason: str = Field(..., description="개선 이유")

