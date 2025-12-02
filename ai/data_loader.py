"""
FAQ 데이터 로더 - XLSX 파일을 읽어 Pinecone에 업로드
"""
import logging
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class FAQDataLoader:
    """FAQ 데이터 로더"""
    
    def __init__(self, file_path: str):
        """
        데이터 로더 초기화
        
        Args:
            file_path: XLSX 파일 경로
        """
        self.file_path = file_path
        logger.info(f"FAQDataLoader 초기화 (파일: {file_path})")
    
    def load_from_xlsx(self) -> List[Dict[str, Any]]:
        """
        XLSX 파일에서 FAQ 데이터 로드
        
        Returns:
            FAQ 데이터 리스트
        """
        try:
            # 파일 존재 확인
            if not Path(self.file_path).exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.file_path}")
            
            # XLSX 파일 읽기 (헤더 없이)
            df = pd.read_excel(self.file_path, header=None)
            
            # 헤더 행 찾기 (Row 6: ['출처', 'Name', 'category', 'keywords', 'question', 'answer'])
            header_row = None
            for idx, row in df.iterrows():
                if row[2] == 'category' or 'category' in str(row.values).lower():
                    header_row = idx
                    break
            
            if header_row is None:
                logger.warning("헤더를 찾을 수 없습니다. 기본 헤더 사용")
                # Row 6부터 읽기 (0-based index이므로 6)
                df = pd.read_excel(self.file_path, header=6)
            else:
                # 헤더 행부터 다시 읽기
                df = pd.read_excel(self.file_path, header=header_row)
            
            logger.info(f"데이터 로드 완료: {len(df)}행, 컬럼: {list(df.columns)}")
            
            # 데이터 파싱
            faq_data = []
            for idx, row in df.iterrows():
                try:
                    # NaN 값 처리
                    category = str(row.get('category', '')).strip() if pd.notna(row.get('category')) else '기타'
                    keywords = str(row.get('keywords', '')).strip() if pd.notna(row.get('keywords')) else ''
                    question = str(row.get('question', '')).strip() if pd.notna(row.get('question')) else ''
                    answer = str(row.get('answer', '')).strip() if pd.notna(row.get('answer')) else ''
                    name = str(row.get('Name', '')).strip() if pd.notna(row.get('Name')) else ''
                    source = str(row.get('출처', '')).strip() if pd.notna(row.get('출처')) else ''
                    
                    # 질문과 답변이 비어있지 않은 경우만 추가
                    if question and answer:
                        # 키워드를 리스트로 변환
                        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
                        
                        faq_item = {
                            'id': f'faq_{idx}',
                            'category': category,
                            'keywords': keyword_list,
                            'question': question,
                            'answer': answer,
                            'name': name,
                            'source': source
                        }
                        faq_data.append(faq_item)
                        
                except Exception as e:
                    logger.warning(f"Row {idx} 파싱 실패: {str(e)}")
                    continue
            
            logger.info(f"유효한 FAQ 데이터: {len(faq_data)}개")
            return faq_data
            
        except Exception as e:
            logger.error(f"XLSX 파일 로드 실패: {str(e)}")
            raise
    
    def prepare_for_pinecone(
        self, 
        faq_data: List[Dict[str, Any]], 
        embeddings: List[List[float]]
    ) -> List[Dict[str, Any]]:
        """
        Pinecone 업로드용 데이터 준비
        
        Args:
            faq_data: FAQ 데이터 리스트
            embeddings: 임베딩 벡터 리스트
            
        Returns:
            Pinecone 벡터 리스트
        """
        if len(faq_data) != len(embeddings):
            raise ValueError(f"데이터 개수({len(faq_data)})와 임베딩 개수({len(embeddings)})가 일치하지 않습니다.")
        
        vectors = []
        for faq, embedding in zip(faq_data, embeddings):
            vector = {
                'id': faq['id'],
                'values': embedding,
                'metadata': {
                    'category': faq['category'],
                    'keywords': ','.join(faq['keywords']),  # 문자열로 저장
                    'question': faq['question'],
                    'answer': faq['answer'],
                    'name': faq.get('name', ''),
                    'source': faq.get('source', '')
                }
            }
            vectors.append(vector)
        
        logger.info(f"Pinecone 벡터 {len(vectors)}개 준비 완료")
        return vectors
    
    def create_text_for_embedding(self, faq_data: List[Dict[str, Any]]) -> List[str]:
        """
        임베딩을 위한 텍스트 생성
        
        Args:
            faq_data: FAQ 데이터 리스트
            
        Returns:
            임베딩용 텍스트 리스트
        """
        texts = []
        for faq in faq_data:
            # 질문 + 키워드 + 답변 결합 (더 풍부한 컨텍스트)
            keywords_str = ', '.join(faq['keywords'])
            text = f"질문: {faq['question']}\n키워드: {keywords_str}\n답변: {faq['answer']}"
            texts.append(text)
        
        logger.info(f"임베딩용 텍스트 {len(texts)}개 생성")
        return texts


def load_and_upload_to_pinecone(
    xlsx_path: str,
    embedding_client,
    pinecone_client,
    force_reload: bool = False
) -> Dict[str, Any]:
    """
    XLSX 파일을 읽어 Pinecone에 업로드하는 헬퍼 함수
    
    Args:
        xlsx_path: XLSX 파일 경로
        embedding_client: EmbeddingClient 인스턴스 (로컬 Sentence Transformers)
        pinecone_client: PineconeClient 인스턴스
        force_reload: 강제 재로드 여부
        
    Returns:
        업로드 결과 정보
    """
    try:
        # 기존 데이터 확인
        stats = pinecone_client.get_index_stats()
        existing_count = stats.get('total_vector_count', 0)
        
        if existing_count > 0 and not force_reload:
            logger.info(f"이미 {existing_count}개의 벡터가 존재합니다. 업로드를 건너뜁니다.")
            return {
                'status': 'skipped',
                'message': f'이미 {existing_count}개의 벡터가 존재합니다.',
                'vector_count': existing_count
            }
        
        if force_reload and existing_count > 0:
            logger.info(f"강제 재로드: 기존 {existing_count}개 벡터 삭제")
            pinecone_client.delete_all()
        
        # 데이터 로드
        loader = FAQDataLoader(xlsx_path)
        faq_data = loader.load_from_xlsx()
        
        if not faq_data:
            raise ValueError("로드된 FAQ 데이터가 없습니다.")
        
        # 임베딩 생성
        logger.info("임베딩 생성 시작...")
        texts = loader.create_text_for_embedding(faq_data)
        embeddings = embedding_client.create_document_embeddings(texts)
        
        # Pinecone 업로드 준비
        vectors = loader.prepare_for_pinecone(faq_data, embeddings)
        
        # Pinecone에 업로드
        logger.info("Pinecone에 업로드 시작...")
        pinecone_client.upsert_vectors(vectors)
        
        # 최종 통계
        final_stats = pinecone_client.get_index_stats()
        
        return {
            'status': 'success',
            'message': f'{len(vectors)}개의 FAQ 데이터가 성공적으로 업로드되었습니다.',
            'vector_count': final_stats.get('total_vector_count', 0),
            'faq_data_count': len(faq_data)
        }
        
    except Exception as e:
        logger.error(f"데이터 업로드 실패: {str(e)}")
        return {
            'status': 'error',
            'message': f'업로드 실패: {str(e)}',
            'vector_count': 0
        }

