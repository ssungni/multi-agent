"""HITL Orchestrator Agent 구현.

lec06_02_hitl의 HITL Base 메커니즘(BaseAgent, BaseAgentState, ToolResult)을 활용하여
아웃라인 승인 단계에서 사용자 인터랙션을 받는 Orchestrator Agent를 정의합니다.

lec06_01_orchestrator의 OrchestratorAgent가 sub-agent 호출만 수행하는 것에 비해,
이 에이전트는 HITL을 통해 아웃라인 승인/수정 루프를 추가합니다.

학습 포인트:
    1. lec06_02_hitl의 BaseAgent를 상속하여 HITL 기능(_resume_hitl, hitl_interrupts) 활용
    2. AskOutlineApprovalTool(mode="tool_result")을 통한 사용자 승인 워크플로우
    3. lec06_01의 sub-agent 호출 도구(CallOutliner, CallResearcher, CallWriter)와의 통합
"""

from typing import Any

from langfuse.decorators import observe
from typing_extensions import Self

from lec05_01_outliner.agent import OutlinerAgent
from lec05_02_researcher.agent import ResearcherWorkflow
from lec05_03_writer.agent import WriterAgent
from lec06_01_orchestrator.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from lec06_01_orchestrator.tools import (
    CallOutlinerTool,
    CallResearcherTool,
    CallWriterTool,
    FinalAnswerTool,
)
from lec06_02_hitl.ask_outline_approval import AskOutlineApprovalTool
from lec06_02_hitl.base import BaseAgent
from lec06_02_hitl.state import HITLOrchestratorState, HITLPhase

# ---------------------------------------------------------------------------
# HITL Orchestrator 도구 구성
# ---------------------------------------------------------------------------

# Constructor injection으로 sub-agent 클래스 전달
call_outliner_tool = CallOutlinerTool(subagent_class=OutlinerAgent)
call_researcher_tool = CallResearcherTool(workflow_class=ResearcherWorkflow)
call_writer_tool = CallWriterTool(subagent_class=WriterAgent)
final_answer_tool = FinalAnswerTool()

# AskOutlineApprovalTool은 lec06_02_hitl.tool.BaseTool을 상속하고,
# 나머지 도구는 lec04_01_base_agent.tool.BaseTool을 상속합니다.
# 두 BaseTool은 동일한 인터페이스의 별도 구현체이므로 런타임에서 호환됩니다.
HITL_ORCHESTRATOR_DEFAULT_TOOLS: list[Any] = [
    call_outliner_tool,
    AskOutlineApprovalTool(),
    call_researcher_tool,
    call_writer_tool,
    final_answer_tool,
]


# ---------------------------------------------------------------------------
# HITL Orchestrator Agent
# ---------------------------------------------------------------------------


class HITLOrchestratorAgent(BaseAgent[HITLOrchestratorState]):
    """HITL이 통합된 Orchestrator Agent.

    lec06_02_hitl의 BaseAgent를 상속하여 HITL 기능(_resume_hitl, hitl_interrupts 감지)을
    활용하며, 다음 워크플로우를 수행합니다:

    1. **아웃라인 생성**: CallOutlinerTool로 OutlinerAgent 호출
    2. **아웃라인 승인**: AskOutlineApprovalTool로 사용자 승인 요청 (HITL 인터럽트)
    3. **리서치**: CallResearcherTool로 ResearcherAgent 호출
    4. **리포트 작성**: CallWriterTool로 WriterAgent 호출
    5. **결과 전달**: FinalAnswerTool로 최종 리포트 전달

    lec06_01의 OrchestratorAgent와 달리, 아웃라인 생성 후 사용자 승인을 거치며
    거부 시 수정 피드백을 반영하여 아웃라인을 재생성합니다.
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        user_request: str,
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 20,
    ) -> Self:
        """새 HITLOrchestratorAgent 인스턴스를 생성하고 초기화합니다.

        Args:
            user_request: 사용자의 리포트 요청
            model: 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
            max_iterations: 최대 반복 횟수 (기본값: 20)

        Returns:
            Self: 초기화된 HITLOrchestratorAgent 인스턴스
        """
        self = await super().setup()

        self.state = HITLOrchestratorState(
            model=model,
            original_request=user_request,
            messages=[
                {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_request},
            ],
        )

        self.tools = list(HITL_ORCHESTRATOR_DEFAULT_TOOLS)
        self.max_iterations = max_iterations
        self.model = model
        self.stream = True

        self._initialized = True
        return self

    def _should_stop(self) -> bool:
        """에이전트가 실행을 중단해야 하는지 확인합니다.

        기본 종료 조건(최대 반복 횟수, HITL 인터럽트)에 더해,
        워크플로우가 완료되었는지 확인합니다.

        Returns:
            bool: 에이전트가 중단해야 하면 True, 계속하려면 False

        Raises:
            MaxIterationError: max_iterations를 초과한 경우
        """
        if super()._should_stop():
            return True
        return self.state.current_phase == HITLPhase.COMPLETE
