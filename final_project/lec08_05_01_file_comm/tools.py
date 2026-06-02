"""파일 기반 커뮤니케이션 도구 모듈.

기존 Orchestrator 도구들을 상속하여 결과를 파일로 저장하고,
파일 경로만 LLM에 반환하는 패턴을 구현합니다.

주요 도구:
- FileCommCallOutlinerTool: 아웃라인 결과를 outline.json으로 저장
- FileCommCallResearcherTool: 리서치 결과를 research.json으로 저장
- FileCommCallWriterTool: 리포트를 report.json으로 저장
- ReadFileTool: 워크스페이스 파일을 읽어 LLM에 반환
"""

import json
from typing import Any

from lec04_01_base_agent.tool import BaseTool, ToolResult
from lec06_01_orchestrator.state import OrchestratorState
from lec06_01_orchestrator.tools import (
    CallOutlinerTool,
    CallResearcherTool,
    CallWriterTool,
)
from lec08_05_01_file_comm.workspace import WorkspaceManager


class FileCommCallOutlinerTool(CallOutlinerTool):
    """파일 기반 Outliner 도구.

    CallOutlinerTool을 상속하여 아웃라인 결과를 outline.json으로 저장하고,
    요약 + 파일 경로만 반환합니다.
    """

    def __init__(self, subagent_class: Any, workspace: WorkspaceManager) -> None:
        """FileCommCallOutlinerTool을 초기화합니다.

        Args:
            subagent_class: 사용할 OutlinerAgent 클래스
            workspace: 파일 저장을 위한 WorkspaceManager
        """
        super().__init__(subagent_class=subagent_class)
        self._workspace = workspace

    async def _execute(self, state: OrchestratorState, **kwargs: Any) -> ToolResult:
        """아웃라인을 생성하고 결과를 파일로 저장합니다.

        Args:
            state: 현재 OrchestratorState
            **kwargs: topic, requirements 등

        Returns:
            파일 경로를 포함한 요약 ToolResult
        """
        result = await super()._execute(state, **kwargs)

        if state.outline:
            filepath = self._workspace.save_json(
                "outline.json",
                state.outline.model_dump(),
            )
            num_sections = len(state.outline.sections)
            content = (
                f"Outline generated: '{state.outline.title}' ({num_sections} sections).\n"
                f"Saved to: {filepath}\n"
                f"Use read_file to inspect details."
            )
            return ToolResult(content=content, artifact=result.artifact)

        return result


class FileCommCallResearcherTool(CallResearcherTool):
    """파일 기반 Researcher 도구.

    CallResearcherTool을 상속하여 리서치 결과를 research.json으로 저장하고,
    요약 + 파일 경로만 반환합니다.
    """

    def __init__(self, workflow_class: Any, workspace: WorkspaceManager) -> None:
        """FileCommCallResearcherTool을 초기화합니다.

        Args:
            workflow_class: 사용할 ResearcherWorkflow 클래스
            workspace: 파일 저장을 위한 WorkspaceManager
        """
        super().__init__(workflow_class=workflow_class)
        self._workspace = workspace

    async def _execute(self, state: OrchestratorState, **kwargs: Any) -> ToolResult:
        """리서치를 수행하고 결과를 파일로 저장합니다.

        Args:
            state: 현재 OrchestratorState
            **kwargs: (없음)

        Returns:
            파일 경로를 포함한 요약 ToolResult
        """
        result = await super()._execute(state, **kwargs)

        if state.research_results:
            filepath = self._workspace.save_json(
                "research.json",
                {k: v.model_dump() for k, v in state.research_results.items()},
            )
            completed = sum(1 for r in state.research_results.values() if r.research_complete)
            total = len(state.research_results)
            total_refs = len(state.reference_documents)
            content = (
                f"Research completed for {completed}/{total} sections. "
                f"{total_refs} references.\n"
                f"Saved to: {filepath}\n"
                f"Use read_file to inspect details."
            )
            return ToolResult(content=content, artifact=result.artifact)

        return result


class FileCommCallWriterTool(CallWriterTool):
    """파일 기반 Writer 도구.

    CallWriterTool을 상속하여 리포트를 report.json으로 저장하고,
    요약 + 파일 경로만 반환합니다.
    """

    def __init__(self, subagent_class: Any, workspace: WorkspaceManager) -> None:
        """FileCommCallWriterTool을 초기화합니다.

        Args:
            subagent_class: 사용할 WriterAgent 클래스
            workspace: 파일 저장을 위한 WorkspaceManager
        """
        super().__init__(subagent_class=subagent_class)
        self._workspace = workspace

    async def _execute(self, state: OrchestratorState, **kwargs: Any) -> ToolResult:
        """리포트를 작성하고 결과를 파일로 저장합니다.

        Args:
            state: 현재 OrchestratorState
            **kwargs: (없음)

        Returns:
            파일 경로를 포함한 요약 ToolResult
        """
        result = await super()._execute(state, **kwargs)

        if state.final_report:
            filepath = self._workspace.save_json(
                "report.json",
                state.final_report.model_dump(),
            )
            num_sections = len(state.final_report.sections)
            num_refs = len(state.final_report.references)
            content = (
                f"Report '{state.final_report.title}' written "
                f"({num_sections} sections, {num_refs} refs).\n"
                f"Saved to: {filepath}\n"
                f"Use read_file to inspect details."
            )
            return ToolResult(content=content, artifact=result.artifact)

        return result


class ReadFileTool(BaseTool[OrchestratorState]):
    """워크스페이스 파일을 읽는 도구.

    LLM이 필요할 때만 파일 내용을 읽어 컨텍스트에 로드합니다.
    이를 통해 context window를 절약하면서도 필요한 정보에 접근할 수 있습니다.
    """

    name = "read_file"
    description = (
        "Read a file from the workspace. Use this to inspect the contents of "
        "outline.json, research.json, or report.json when you need to verify "
        "or reference specific details."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to read",
            },
        },
        "required": ["file_path"],
        "additionalProperties": False,
    }

    def __init__(self, workspace: WorkspaceManager) -> None:
        """ReadFileTool을 초기화합니다.

        Args:
            workspace: 파일 읽기를 위한 WorkspaceManager
        """
        self._workspace = workspace

    async def _execute(self, state: OrchestratorState, **kwargs: Any) -> ToolResult:
        """파일을 읽어 내용을 반환합니다.

        Args:
            state: 현재 OrchestratorState (사용하지 않음)
            **kwargs: file_path (str)

        Returns:
            파일 내용을 담은 ToolResult
        """
        _ = state
        file_path: str = kwargs.get("file_path", "")

        if not file_path:
            return ToolResult(content="Error: file_path is required", artifact=None)

        try:
            data = self._workspace.read_json(file_path)
            content = json.dumps(data, ensure_ascii=False, indent=2)
            return ToolResult(content=content, artifact=data)
        except FileNotFoundError:
            return ToolResult(
                content=f"Error: File not found: {file_path}",
                artifact=None,
            )
        except json.JSONDecodeError:
            return ToolResult(
                content=f"Error: Invalid JSON in file: {file_path}",
                artifact=None,
            )
