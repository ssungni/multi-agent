"""Orchestrator Agent 상태 관리 모듈.

전체 리포트 생성 워크플로우의 상태를 추적하는 OrchestratorState를 정의합니다.
"""

from enum import Enum

from lec04_01_base_agent.state import BaseAgentState
from lec04_02_tools.schemas import ReferenceDocument
from lec05_01_outliner.schemas import Outline
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer.schemas import FinalReport


class Phase(str, Enum):
    """Orchestrator의 워크플로우 단계.

    Attributes:
        OUTLINE_GENERATION: 아웃라인 생성 단계
        RESEARCH: 섹션별 리서치 단계
        WRITING: 리포트 작성 단계
        COMPLETE: 워크플로우 완료
    """

    OUTLINE_GENERATION = "outline_generation"
    RESEARCH = "research"
    WRITING = "writing"
    COMPLETE = "complete"


class OrchestratorState(BaseAgentState):
    """Orchestrator Agent의 상태를 관리하는 모델.

    전체 리포트 생성 워크플로우의 진행 상황과 각 sub-agent의 출력물을 추적합니다.

    Attributes:
        original_request: 사용자의 원본 리포트 요청
        current_phase: 현재 워크플로우 단계
        outline: Outliner Agent가 생성한 아웃라인
        research_results: 섹션 제목을 키로 하는 리서치 결과 딕셔너리
        final_report: Writer Agent가 생성한 최종 리포트
        reference_documents: 수집된 참조 문서 리스트
    """

    original_request: str
    current_phase: str = Phase.OUTLINE_GENERATION
    outline: Outline | None = None
    research_results: dict[str, SectionResearch] = {}
    final_report: FinalReport | None = None
    reference_documents: list[ReferenceDocument] = []
