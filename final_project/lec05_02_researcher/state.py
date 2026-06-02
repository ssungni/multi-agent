"""Researcher Workflow 상태 관리 모듈.

Researcher Workflow의 실행 결과를 저장하는 ResearcherState 모델을 정의합니다.
워크플로우의 각 단계(필요 정보 정의, 병렬 리서치, 중복 제거) 결과를 관리합니다.
"""

from pydantic import BaseModel

from lec04_02_tools.schemas import ReferenceDocument
from lec05_01_outliner.schemas import Outline
from lec05_02_researcher.schemas import SectionResearch


class ResearcherState(BaseModel):
    """Researcher Workflow의 결과 상태를 관리하는 모델.

    Attributes:
        outline: Outliner Agent가 생성한 아웃라인
        section_research_results: 섹션 제목을 키로 하는 리서치 결과 딕셔너리
        reference_documents: 중복 제거된 참조 문서 리스트
    """

    outline: Outline | None = None
    section_research_results: dict[str, SectionResearch] = {}
    reference_documents: list[ReferenceDocument] = []
