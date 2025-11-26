"""
슬랙 연동 서비스
"""
import time
import uuid
import logging
import re
from typing import Optional, Dict, List, Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from database.connection import get_db_connection
from models.schemas import SlackIssue
from config.settings import SLACK_CHANNEL_ID

logger = logging.getLogger(__name__)

def parse_slack_issue_message(text: str, user_name: str = None) -> Optional[Dict[str, str]]:
    """슬랙 메시지에서 이슈 정보를 파싱합니다."""
    # 멘션 태그가 포함된 메시지인지 확인
    has_mention = any(mention in text for mention in ["<@here>", "<@everyone>", "<@channel>", "<!here>", "<!everyone>", "<!channel>"])
    
    # 특정 사용자들의 메시지인지 확인
    target_users = ["장지연", "김은지"]
    is_target_user = user_name and user_name in target_users
    
    # 멘션이나 특정 사용자가 아니면 None 반환
    if not has_mention and not is_target_user:
        return None
    
    # 기본 정보 추출
    issue_data = {}
    
    # 과정/프로젝트 추출
    project_match = re.search(r'과정[:：]\s*([^\n]+)', text)
    if project_match:
        issue_data['project'] = project_match.group(1).strip()
    else:
        # 키워드 기반으로 프로젝트 추정
        if any(keyword in text for keyword in ["프론트엔드", "frontend", "Front-end", "React", "Vue", "Angular"]):
            issue_data['project'] = "프론트엔드 관련"
        elif any(keyword in text for keyword in ["백엔드", "backend", "Back-end", "Django", "Spring", "Node.js"]):
            issue_data['project'] = "백엔드 관련"
        elif any(keyword in text for keyword in ["훈련장려금", "장려금", "출결", "공결"]):
            issue_data['project'] = "행정 관련"
        else:
            issue_data['project'] = "일반 공지"
    
    # 내용 추출
    content_match = re.search(r'내용[:：]\s*([^\n]+)', text)
    if content_match:
        issue_data['content'] = content_match.group(1).strip()
    else:
        # 멘션 태그를 제거하고 메시지 내용만 추출
        content = re.sub(r'<@[^>]+>', '', text).strip()
        content = re.sub(r'<!here>|<!everyone>|<!channel>', '', content).strip()
        issue_data['content'] = content if content else "멘션 메시지"
    
    # 작성자 추출
    author_match = re.search(r'작성자[:：]\s*([^\n]+)', text)
    if author_match:
        issue_data['author'] = author_match.group(1).strip()
    elif is_target_user:
        issue_data['author'] = user_name
    else:
        issue_data['author'] = "행정 담당자"
    
    # 이슈 유형 분류
    issue_type = "일반"
    if any(keyword in text for keyword in ["프론트엔드", "frontend", "Front-end", "React", "Vue", "Angular"]):
        issue_type = "프론트엔드"
    elif any(keyword in text for keyword in ["백엔드", "backend", "Back-end", "Django", "Spring", "Node.js"]):
        issue_type = "백엔드"
    elif any(keyword in text for keyword in ["훈련장려금", "장려금"]):
        issue_type = "훈련장려금"
    elif any(keyword in text for keyword in ["환경설정", "설정", "환경"]):
        issue_type = "환경설정"
    elif any(keyword in text for keyword in ["출결", "공결", "지각", "조퇴", "결석"]):
        issue_type = "출결관리"
    elif any(keyword in text for keyword in ["공지", "안내", "알림"]):
        issue_type = "공지사항"
    elif is_target_user:
        issue_type = "담당자 메시지"
    
    issue_data['issue_type'] = issue_type
    
    return issue_data

def save_slack_issue(
    issue_data: Dict[str, str], 
    raw_message: str, 
    channel_id: str = None, 
    timestamp: str = None, 
    slack_ts: str = None
) -> str:
    """파싱된 슬랙 이슈를 데이터베이스에 저장합니다."""
    import psycopg2
    conn = get_db_connection()
    cursor = conn.cursor()
    
    issue_id = str(uuid.uuid4())
    
    try:
        cursor.execute('''
            INSERT INTO slack_issues (id, project, issue_type, author, content, raw_message, channel_id, timestamp, slack_ts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            issue_id,
            issue_data['project'],
            issue_data['issue_type'],
            issue_data['author'],
            issue_data['content'],
            raw_message,
            channel_id,
            timestamp,
            slack_ts
        ))
        
        conn.commit()
        logger.info(f"슬랙 이슈 저장 완료: {issue_id}")
        return issue_id
        
    except psycopg2.IntegrityError as e:
        if "duplicate key value" in str(e):
            logger.info(f"이미 존재하는 슬랙 메시지: {slack_ts}")
            return None
        raise
    finally:
        conn.close()

def get_slack_issues(limit: int = 50, project: str = None) -> List[SlackIssue]:
    """저장된 슬랙 이슈들을 조회합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if project:
            cursor.execute('''
                SELECT id, project, issue_type, author, content, raw_message, channel_id, timestamp, slack_ts, created_at
                FROM slack_issues 
                WHERE project LIKE %s
                ORDER BY created_at DESC 
                LIMIT %s
            ''', (f'%{project}%', limit))
        else:
            cursor.execute('''
                SELECT id, project, issue_type, author, content, raw_message, channel_id, timestamp, slack_ts, created_at
                FROM slack_issues 
                ORDER BY created_at DESC 
                LIMIT %s
            ''', (limit,))
        
        rows = cursor.fetchall()
        issues = []
        
        for row in rows:
            created_at_str = row[9].isoformat() if hasattr(row[9], 'isoformat') else str(row[9])
            
            issues.append(SlackIssue(
                id=row[0],
                project=row[1],
                issue_type=row[2],
                author=row[3],
                content=row[4],
                raw_message=row[5],
                channel_id=row[6],
                timestamp=row[7],
                slack_ts=row[8],
                created_at=created_at_str
            ))
        
        return issues
        
    finally:
        conn.close()

async def fetch_slack_messages(slack_client: WebClient, hours: int = 24) -> List[Dict[str, Any]]:
    """슬랙 채널에서 메시지를 가져옵니다."""
    if not slack_client:
        raise Exception("슬랙 클라이언트가 초기화되지 않았습니다")
    
    try:
        # 지정된 시간 이전의 타임스탬프 계산
        oldest_time = time.time() - (hours * 3600)
        
        # 채널 메시지 가져오기
        response = slack_client.conversations_history(
            channel=SLACK_CHANNEL_ID,
            oldest=str(oldest_time),
            limit=100
        )
        
        if not response["ok"]:
            raise Exception(f"슬랙 API 오류: {response.get('error', 'Unknown error')}")
        
        return response["messages"]
        
    except SlackApiError as e:
        logger.error(f"슬랙 API 오류: {e}")
        error_detail = f"슬랙 API 오류: {e.response['error'] if hasattr(e, 'response') and e.response else str(e)}"
        raise Exception(error_detail)

async def sync_slack_issues(slack_client: WebClient, hours: int = 24, force: bool = False) -> Dict[str, Any]:
    """슬랙 채널에서 이슈 메시지를 동기화합니다."""
    try:
        messages = await fetch_slack_messages(slack_client, hours)
        
        new_issues = 0
        skipped_issues = 0
        errors = 0
        
        for message in messages:
            # 봇 메시지나 편집된 메시지는 무시
            if message.get("bot_id") or message.get("subtype") == "message_changed":
                continue
            
            text = message.get("text", "")
            slack_ts = message.get("ts")
            user_id = message.get("user", "")
            
            # 사용자 정보 가져오기
            user_name = None
            if user_id:
                try:
                    user_info = slack_client.users_info(user=user_id)
                    if user_info["ok"]:
                        user_name = user_info["user"].get("real_name", "")
                except Exception as e:
                    logger.warning(f"사용자 정보 조회 실패: {e}")
            
            # 이슈 메시지인지 파싱 시도
            issue_data = parse_slack_issue_message(text, user_name)
            if not issue_data:
                continue
            
            try:
                # 데이터베이스에 저장
                issue_id = save_slack_issue(
                    issue_data=issue_data,
                    raw_message=text,
                    channel_id=SLACK_CHANNEL_ID,
                    timestamp=message.get("ts"),
                    slack_ts=slack_ts
                )
                
                if issue_id:
                    new_issues += 1
                    logger.info(f"새로운 이슈 저장: {issue_data['project']} - {issue_data['content'][:50]}...")
                else:
                    skipped_issues += 1
                    
            except Exception as e:
                logger.error(f"이슈 저장 중 오류: {e}")
                errors += 1
        
        return {
            "success": True,
            "message": f"동기화 완료: 새로운 이슈 {new_issues}개, 건너뛴 이슈 {skipped_issues}개, 오류 {errors}개",
            "new_issues": new_issues,
            "skipped_issues": skipped_issues,
            "errors": errors,
            "total_messages": len(messages)
        }
        
    except Exception as e:
        logger.error(f"슬랙 동기화 오류: {e}", exc_info=True)
        error_msg = str(e) if str(e) else f"알 수 없는 오류: {type(e).__name__}"
        return {
            "success": False,
            "message": f"동기화 실패: {error_msg}",
            "new_issues": 0,
            "skipped_issues": 0,
            "errors": 1,
            "error_details": {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "slack_client_available": bool(slack_client),
                "slack_channel_id": SLACK_CHANNEL_ID
            }
        }

