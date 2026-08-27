"""Search Agent 상태 관리 모듈.

SearchAgent의 실행 상태를 추적하는 SearchAgentState 모델을 정의합니다.
개별 섹션에 대한 리서치 파이프라인 실행 과정의 상태를 관리합니다.
"""

from lec04_01_base_agent.state import BaseAgentState
from lec04_02_tools.schemas import ReferenceDocument
from lec05_02_researcher.schemas import RequiredInfo, SectionResearch


class SearchAgentState(BaseAgentState):
    """Search Agent의 상태를 관리하는 모델.

    개별 섹션에 대해 웹 검색과 콘텐츠 수집을 수행하는 과정의 상태를 추적합니다.

    Attributes:
        section_title: 리서치 대상 섹션의 제목
        section_description: 리서치 대상 섹션의 설명
        required_info: 섹션 작성에 필요한 정보 항목 리스트
        section_research: 섹션 리서치 결과 (SubmitResearchTool 호출 시 생성)
        reference_documents: 검색 및 페치로 수집된 참조 문서 리스트
    """

    section_title: str = ""
    section_description: str = ""
    required_info: list[RequiredInfo] = []
    section_research: SectionResearch | None = None
    reference_documents: list[ReferenceDocument] = []
    submitted_research: bool = False
