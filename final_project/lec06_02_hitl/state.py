"""HITL 지원이 포함된 에이전트 상태 관리.

lec04_01_base_agent/state.py를 확장하여 HITL 기능을 추가합니다.

이 모듈은 BaseAgentState에 HITL (Human-In-The-Loop) 기능을 확장합니다.
hitl_interrupts 필드는 에이전트 실행을 일시정지하는 대기 중인 사용자 입력을 저장합니다.

또한 HITL Orchestrator를 위한 HITLPhase와 HITLOrchestratorState를 정의합니다.
"""

import warnings
from enum import Enum
from typing import TypeVar

warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

from litellm.types.completion import ChatCompletionMessageParam
from pydantic import BaseModel, SkipValidation
from typing_extensions import Annotated

from lec04_02_tools.schemas import ReferenceDocument
from lec05_01_outliner.schemas import Outline
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer.schemas import FinalReport
from lec06_02_hitl.hitl import HITLData


class BaseAgentState(BaseModel):
    """HITL 지원이 포함된 모든 에이전트를 위한 기본 상태 모델.

    이 모델은 에이전트 실행 루프에 필요한 필수 상태를 추적합니다:
    - 사용할 LLM 모델
    - 대화 기록 (messages)
    - 현재 반복 횟수
    - 사용자 응답 대기 중인 HITL 인터럽트 (lec06_02_hitl에서 추가)

    Attributes:
        model: LLM 모델 식별자 (예: "gpt-4", "claude-3-sonnet-20240229")
        messages: 채팅 완료 메시지 리스트로 된 대화 기록
        iteration_count: 에이전트 루프의 현재 반복 번호 (0부터 시작)
        hitl_interrupts: 사용자 응답을 기다리는 HITL 인터럽트 리스트 (lec06_02_hitl에서 추가)
    """

    model: str = "claude-4.5-sonnet"
    messages: Annotated[list[ChatCompletionMessageParam], SkipValidation] = []
    iteration_count: int = 0
    hitl_interrupts: list[HITLData] = []  # [ADDED in lec06_02_hitl]

    @property
    def working_messages(self) -> list[ChatCompletionMessageParam]:
        """컨텍스트 관리에 사용되는 메시지를 반환합니다.

        이 기본 버전에서는 모든 메시지를 단순히 반환합니다. 이후 강의에서
        컨텍스트 윈도우 관리 (압축, 요약 등)를 구현하도록 확장될 것입니다.

        Returns:
            LLM에 전송할 메시지 리스트
        """
        return self.messages


# 에이전트 상태를 위한 제네릭 타입 변수
# 서브클래스가 타입 안전성을 유지하면서 자체 상태 타입을 정의할 수 있게 합니다
TState = TypeVar("TState", bound=BaseAgentState)


class HITLPhase(str, Enum):
    """HITL Orchestrator의 워크플로우 단계.

    lec06_01의 Phase에 OUTLINE_APPROVAL 단계를 추가합니다.

    Attributes:
        OUTLINE_GENERATION: 아웃라인 생성 단계
        OUTLINE_APPROVAL: 아웃라인 승인 단계 (HITL 인터럽트 발생)
        RESEARCH: 섹션별 리서치 단계
        WRITING: 리포트 작성 단계
        COMPLETE: 워크플로우 완료
    """

    OUTLINE_GENERATION = "outline_generation"
    OUTLINE_APPROVAL = "outline_approval"
    RESEARCH = "research"
    WRITING = "writing"
    COMPLETE = "complete"


class HITLOrchestratorState(BaseAgentState):
    """HITL Orchestrator의 상태.

    BaseAgentState를 상속하여 hitl_interrupts 필드를 포함하면서,
    lec06_01 OrchestratorState와 동일한 워크플로우 필드를 정의합니다.

    Attributes:
        original_request: 사용자의 원본 리포트 요청
        current_phase: 현재 워크플로우 단계
        outline: Outliner Agent가 생성한 아웃라인
        research_results: 섹션 제목을 키로 하는 리서치 결과 딕셔너리
        final_report: Writer Agent가 생성한 최종 리포트
        reference_documents: 수집된 참조 문서 리스트
        outline_approved: 아웃라인 승인 여부
    """

    original_request: str
    current_phase: str = HITLPhase.OUTLINE_GENERATION  # [ADDED in lec06_02_hitl]
    outline: Outline | None = None
    research_results: dict[str, SectionResearch] = {}
    final_report: FinalReport | None = None
    reference_documents: list[ReferenceDocument] = []
    outline_approved: bool = False  # [ADDED in lec06_02_hitl]
