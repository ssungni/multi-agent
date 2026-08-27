"""파일 기반 커뮤니케이션 Orchestrator Agent.

OptimizedOrchestratorAgent를 상속하여 도구 결과를 파일로 저장하고,
파일 경로만 LLM에 전달하는 방식으로 컨텍스트 윈도우를 절약합니다.

상속 체인:
    OrchestratorAgent (lec06_01)
    └── OptimizedOrchestratorAgent (lec08_04)
        └── FileCommOrchestratorAgent (this file)
"""

from typing_extensions import Self

from lec06_01_orchestrator.tools import FinalAnswerTool
from lec08_04_cost.main import (
    OptimizedOrchestratorAgent,
    OptimizedOutlinerAgent,
    OptimizedResearcherWorkflow,
    OptimizedWriterAgent,
)
from lec08_05_01_file_comm.prompts import FILE_COMM_SYSTEM_PROMPT
from lec08_05_01_file_comm.tools import (
    FileCommCallOutlinerTool,
    FileCommCallResearcherTool,
    FileCommCallWriterTool,
    ReadFileTool,
)
from lec08_05_01_file_comm.workspace import WorkspaceManager


class FileCommOrchestratorAgent(OptimizedOrchestratorAgent):
    """파일 기반 커뮤니케이션이 적용된 OrchestratorAgent.

    OptimizedOrchestratorAgent를 상속하여:
    1. 기존 최적화(ModelSelector, Cache Control 등) 유지
    2. 도구 결과를 파일로 저장하여 컨텍스트 윈도우 절약
    3. ReadFileTool로 필요할 때만 파일 내용 조회

    오버라이드 메서드:
        setup(): WorkspaceManager 생성, FileComm 도구 교체, 시스템 프롬프트 변경
    """

    workspace: WorkspaceManager | None = None

    @classmethod
    async def setup(  # type: ignore[override]
        cls,
        user_request: str,
        max_iterations: int = 20,
    ) -> Self:
        """FileCommOrchestratorAgent를 생성합니다.

        OptimizedOrchestratorAgent.setup()을 호출하여 기존 최적화를 유지한 후,
        도구를 FileComm 버전으로 교체하고 시스템 프롬프트를 변경합니다.

        Args:
            user_request: 사용자의 리포트 요청
            max_iterations: 최대 반복 횟수

        Returns:
            초기화된 FileCommOrchestratorAgent 인스턴스
        """
        self = await super().setup(
            user_request=user_request,
            max_iterations=max_iterations,
        )

        # WorkspaceManager 생성
        self.workspace = WorkspaceManager()

        # 기존 도구를 FileComm 버전으로 교체 + ReadFileTool 추가
        self.tools = [
            FileCommCallOutlinerTool(
                subagent_class=OptimizedOutlinerAgent,
                workspace=self.workspace,
            ),
            FileCommCallResearcherTool(
                workflow_class=OptimizedResearcherWorkflow,
                workspace=self.workspace,
            ),
            FileCommCallWriterTool(
                subagent_class=OptimizedWriterAgent,
                workspace=self.workspace,
            ),
            ReadFileTool(workspace=self.workspace),
            FinalAnswerTool(),
        ]

        # 시스템 프롬프트를 파일 기반 버전으로 교체
        if self.state.messages and self.state.messages[0].get("role") == "system":
            self.state.messages[0] = {
                "role": "system",
                "content": FILE_COMM_SYSTEM_PROMPT,
            }

        return self
