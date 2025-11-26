"""
Claude API 클라이언트
"""
import logging
from typing import Optional
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ClaudeAPIClient:
    def __init__(self, api_key):
        """Claude API 클라이언트 초기화"""
        if not api_key:
            raise ValueError("Anthropic API 키가 제공되지 않았습니다.")
        
        self.logger = logging.getLogger(__name__)
        self.model = "claude-3-haiku-20240307"  # 가장 빠르고 저렴한 모델
        
        # Anthropic 클라이언트 초기화
        self.client = Anthropic(api_key=api_key)
        
        self.logger.info(f"ClaudeAPIClient 초기화 완료 (모델: {self.model})")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def make_request(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Claude API 요청 수행"""
        self.logger.info(f"Claude API 요청 시작 (프롬프트 길이: {len(prompt)} 문자)")
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if response and response.content and len(response.content) > 0:
                result = response.content[0].text
                self.logger.info("Claude API 요청 성공")
                return result
            else:
                self.logger.error("Claude API 응답이 비어있음")
                raise Exception("Claude API 응답이 비어있습니다")
                
        except Exception as e:
            self.logger.error(f"Claude API 요청 실패: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Claude API 연결 테스트"""
        try:
            self.logger.info("Claude API 연결 테스트 시작")
            result = self.make_request("안녕하세요", max_tokens=10)
            return bool(result)
        except Exception as e:
            self.logger.error(f"Claude API 연결 테스트 실패: {str(e)}")
            return False

