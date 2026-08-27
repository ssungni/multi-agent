"""ExtendedHITLData를 지원하는 확장된 에이전트 상태.

lec06_02_hitl.state.BaseAgentState의 hitl_interrupts 필드는 list[HITLData] 타입입니다.
ExtendedHITLData를 저장하려면 타입을 확장한 상태가 필요합니다.

또한 ExtendedOrchestratorState를 정의하여 lec06_02_hitl의 HITLOrchestratorState와
동일한 워크플로우 필드를 ExtendedAgentState 기반으로 제공합니다.
"""

from typing import TypeVar

from litellm.types.completion import ChatCompletionMessageParam
from pydantic import BaseModel, SkipValidation
from typing_extensions import Annotated

from lec04_02_tools.schemas import ReferenceDocument
from lec05_01_outliner.schemas import Outline
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer.schemas import FinalReport
from lec06_02_hitl.state import HITLPhase
from lec07_02_ask_user.hitl import ExtendedHITLData


class ExtendedAgentState(BaseModel):
    """ExtendedHITLData를 지원하는 확장된 에이전트 상태.

    lec06_02_hitl.state.BaseAgentState와 동일한 필드를 가지되,
    hitl_interrupts의 타입이 list[ExtendedHITLData]로 확장됩니다.

    Attributes:
        model: LLM 모델 식별자
        messages: 대화 기록
        iteration_count: 현재 반복 번호
        hitl_interrupts: 사용자 응답을 기다리는 HITL 인터럽트 리스트 (ExtendedHITLData)
    """

    model: str = "claude-4.5-sonnet"
    messages: Annotated[list[ChatCompletionMessageParam], SkipValidation] = []
    iteration_count: int = 0
    hitl_interrupts: list[ExtendedHITLData] = []  # [ADDED in lec07_02_ask_user]

    @property
    def working_messages(self) -> list[ChatCompletionMessageParam]:
        """컨텍스트 관리에 사용되는 메시지를 반환합니다."""
        return self.messages


TExtendedState = TypeVar("TExtendedState", bound=ExtendedAgentState)


class ExtendedOrchestratorState(ExtendedAgentState):  # [ADDED in lec07_02_ask_user]
    """ExtendedHITLData를 지원하는 Orchestrator 상태.

    lec06_02_hitl.state.HITLOrchestratorState와 동일한 워크플로우 필드를 가지되,
    ExtendedAgentState를 상속하여 hitl_interrupts가 list[ExtendedHITLData] 타입입니다.
    이를 통해 tool_call 모드(ask_user_question)와 tool_result 모드(ask_outline_approval)를
    모두 지원할 수 있습니다.

    Attributes:
        original_request: 사용자의 원본 리포트 요청
        current_phase: 현재 워크플로우 단계 (HITLPhase)
        outline: Outliner Agent가 생성한 아웃라인
        research_results: 섹션 제목을 키로 하는 리서치 결과 딕셔너리
        final_report: Writer Agent가 생성한 최종 리포트
        reference_documents: 수집된 참조 문서 리스트
        outline_approved: 아웃라인 승인 여부
    """

    original_request: str
    current_phase: str = HITLPhase.OUTLINE_GENERATION
    outline: Outline | None = None
    research_results: dict[str, SectionResearch] = {}
    final_report: FinalReport | None = None
    reference_documents: list[ReferenceDocument] = []
    outline_approved: bool = False
