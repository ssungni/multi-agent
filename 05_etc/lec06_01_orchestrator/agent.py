"""Orchestrator Agent 구현.

Sub-agent들을 조율하여 전체 리포트 생성 워크플로우를 관리하는
OrchestratorAgent를 정의합니다.
"""

from langfuse.decorators import observe
from typing_extensions import Self

from lec04_01_base_agent.base import BaseAgent
from lec04_01_base_agent.tool import BaseTool
from lec05_01_outliner.agent import OutlinerAgent
from lec05_02_researcher.agent import ResearcherWorkflow
from lec05_03_writer.agent import WriterAgent
from lec06_01_orchestrator.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from lec06_01_orchestrator.state import OrchestratorState, Phase
from lec06_01_orchestrator.tools import (
    CallOutlinerTool,
    CallResearcherTool,
    CallWriterTool,
    FinalAnswerTool,
)

# Constructor injection으로 sub-agent 클래스 전달
call_outliner_tool = CallOutlinerTool(subagent_class=OutlinerAgent)
call_researcher_tool = CallResearcherTool(workflow_class=ResearcherWorkflow)
call_writer_tool = CallWriterTool(subagent_class=WriterAgent)
final_answer_tool = FinalAnswerTool()

# Default tools for OrchestratorAgent
ORCHESTRATOR_DEFAULT_TOOLS: list[BaseTool] = [
    call_outliner_tool,
    call_researcher_tool,
    call_writer_tool,
    final_answer_tool,
]


class OrchestratorAgent(BaseAgent[OrchestratorState]):
    """전체 리포트 생성 워크플로우를 관리하는 오케스트레이터 에이전트.

    이 에이전트는 다음 단계를 순차적으로 수행합니다:

    1. **아웃라인 생성**: OutlinerAgent를 호출하여 구조화된 아웃라인 생성
    2. **리서치**: ResearcherWorkflow를 호출하여 섹션별 정보 수집
    3. **리포트 작성**: WriterAgent를 호출하여 최종 리포트 작성
    4. **결과 전달**: FinalAnswerTool로 최종 리포트를 사용자에게 전달

    각 sub-agent는 독립적으로 동작하며, Orchestrator가 이들 간의
    데이터 흐름과 상태 전환을 관리합니다.

    Attributes:
        state: 에이전트의 실행 상태 (OrchestratorState)
        tools: 사용 가능한 도구 목록
        max_iterations: 최대 반복 횟수
        model: 사용할 LLM 모델 이름
        stream: 스트리밍 모드 사용 여부

    Example:
        >>> agent = await OrchestratorAgent.setup(
        ...     user_request="2025년 생성형 AI 시장 동향에 대한 리포트 작성",
        ...     model="claude-4.5-sonnet",
        ...     max_iterations=20,
        ... )
        >>> await agent.run()
        >>> print(agent.state.final_report.title)
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        user_request: str,
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 20,
    ) -> Self:
        """새 OrchestratorAgent 인스턴스를 생성하고 초기화합니다.

        Args:
            user_request: 사용자의 리포트 요청
            model: 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
            max_iterations: 최대 반복 횟수 (기본값: 20)

        Returns:
            Self: 초기화된 OrchestratorAgent 인스턴스

        Raises:
            RuntimeError: setup()이 이미 초기화된 에이전트에서 호출된 경우
        """
        self = await super().setup()

        # 상태 초기화
        self.state = OrchestratorState(
            model=model,
            original_request=user_request,
            messages=[
                {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_request},
            ],
        )

        # 도구 등록
        self.tools = list(ORCHESTRATOR_DEFAULT_TOOLS)

        # 에이전트 설정
        self.max_iterations = max_iterations
        self.model = model
        self.stream = True

        self._initialized = True
        return self

    def _should_stop(self) -> bool:
        """에이전트가 실행을 중단해야 하는지 확인합니다.

        기본 종료 조건(최대 반복 횟수)에 더해, 워크플로우가 완료되었는지 확인합니다.

        Returns:
            bool: 에이전트가 중단해야 하면 True, 계속하려면 False

        Raises:
            MaxIterationError: max_iterations를 초과한 경우
        """
        if super()._should_stop():
            return True
        return self.state.current_phase == Phase.COMPLETE
