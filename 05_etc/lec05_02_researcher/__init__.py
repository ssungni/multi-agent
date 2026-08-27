"""Lecture 05-02: ResearcherWorkflow implementation - 섹션별 리서치.

이 패키지는 Report Generation Agent의 Researcher 컴포넌트를 포함합니다:
- ResearcherWorkflow: 워크플로우 형태의 리서치 파이프라인
- SearchAgent: 개별 섹션 리서치를 수행하는 서브에이전트
- ResearcherState: Researcher 결과 상태 모델
- SearchAgentState: SearchAgent 상태 관리 모델
- RequiredInfoEvaluator: 필요 정보 정의 품질 평가기
- SectionResearch, RequiredInfo: 리서치 스키마

워크플로우 흐름:
    필요 정보 정의 (LLM + Evaluator 루프) → 병렬 SearchAgent 실행 → 중복 제거
"""

from lec05_02_researcher.agent import ResearcherWorkflow
from lec05_02_researcher.evaluator import (
    RequiredInfoEvaluationResult,
    RequiredInfoEvaluator,
)
from lec05_02_researcher.schemas import (
    RequiredInfo,
    RequiredInfoDefinition,
    SectionRequiredInfo,
    SectionResearch,
)
from lec05_02_researcher.search_agent import SearchAgent
from lec05_02_researcher.search_agent_state import SearchAgentState
from lec05_02_researcher.search_agent_tools import SubmitResearchTool
from lec05_02_researcher.state import ResearcherState

__all__ = [
    "ResearcherWorkflow",
    "ResearcherState",
    "SearchAgent",
    "SearchAgentState",
    "RequiredInfoEvaluator",
    "RequiredInfoEvaluationResult",
    "SectionResearch",
    "SectionRequiredInfo",
    "RequiredInfoDefinition",
    "RequiredInfo",
    "SubmitResearchTool",
]
