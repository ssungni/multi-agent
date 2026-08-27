"""Orchestrator Agent 도구 모듈.

Sub-agent 호출 도구와 최종 답변 도구를 제공합니다.
Constructor injection 패턴을 사용하여 순환 import를 방지합니다.
"""

from typing import Any

from lec04_01_base_agent.base import BaseAgent
from lec04_01_base_agent.tool import BaseTool, ToolResult
from lec05_01_outliner.state import OutlinerState
from lec05_03_writer.schemas import FinalReport
from lec05_03_writer.state import WriterState
from lec06_01_orchestrator.state import OrchestratorState, Phase


class CallOutlinerTool(BaseTool[OrchestratorState]):
    """Outliner Agent를 호출하여 아웃라인을 생성합니다.

    사용자의 주제와 요구사항을 OutlinerAgent에 전달하고,
    생성된 아웃라인을 부모 상태에 병합합니다.
    Constructor injection으로 순환 import를 방지합니다.
    """

    name = "call_outliner"
    description = (
        "Call the Outliner Agent to generate a structured report outline. "
        "The agent will search the web, collect information, and produce "
        "a quality-evaluated outline."
    )
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The report topic",
            },
            "requirements": {
                "type": "string",
                "description": (
                    "Clarified requirements for the report (scope, audience, depth, etc.)"
                ),
            },
        },
        "required": ["topic"],
        "additionalProperties": False,
    }

    def __init__(self, subagent_class: type[BaseAgent[OutlinerState]]) -> None:
        """CallOutlinerTool을 초기화합니다.

        Args:
            subagent_class: 사용할 OutlinerAgent 클래스
        """
        self._subagent_class = subagent_class

    async def _execute(self, state: OrchestratorState, **kwargs: Any) -> ToolResult:
        """OutlinerAgent를 생성하고 실행하여 아웃라인을 생성합니다.

        Args:
            state: 현재 OrchestratorState
            **kwargs: topic (str), requirements (str)

        Returns:
            아웃라인 생성 결과를 담은 ToolResult

        Raises:
            ValueError: topic이 제공되지 않은 경우
        """
        topic: str = kwargs.get("topic", "")
        requirements: str = kwargs.get("requirements", "")

        if not topic:
            raise ValueError("topic is required")

        # Sub-agent 생성 및 실행
        agent = await self._subagent_class.setup(
            topic=topic,
            clarified_requirements=requirements,
            model=state.model,
        )
        await agent.run()

        # 결과를 부모 상태에 병합
        state.outline = agent.state.outline
        state.reference_documents.extend(getattr(agent.state, "reference_documents", []))
        state.current_phase = Phase.RESEARCH

        # 결과 메시지 구성
        if state.outline:
            sections_summary = "\n".join(
                f"  {i}. {s.title}: {s.description}"
                for i, s in enumerate(state.outline.sections, 1)
            )
            content = (
                f"Outline generated successfully: '{state.outline.title}'\n"
                f"Sections ({len(state.outline.sections)}):\n{sections_summary}"
            )
        else:
            content = "Outline generation completed but no outline was produced."

        return ToolResult(
            content=content,
            artifact=state.outline.model_dump() if state.outline else None,
        )


class CallResearcherTool(BaseTool[OrchestratorState]):
    """ResearcherWorkflow를 호출하여 섹션별 리서치를 수행합니다.

    생성된 아웃라인을 ResearcherWorkflow에 전달하고,
    수집된 리서치 결과를 부모 상태에 병합합니다.
    """

    name = "call_researcher"
    description = (
        "Call the Researcher Agent to collect information for each section of the outline. "
        "The agent will define required info, search the web, and compile research results. "
        "Must be called after outline generation."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, workflow_class: type[Any]) -> None:
        """CallResearcherTool을 초기화합니다.

        Args:
            workflow_class: 사용할 ResearcherWorkflow 클래스
        """
        self._workflow_class = workflow_class

    async def _execute(self, state: OrchestratorState, **kwargs: Any) -> ToolResult:
        """ResearcherWorkflow를 생성하고 실행하여 섹션별 리서치를 수행합니다.

        Args:
            state: 현재 OrchestratorState
            **kwargs: (없음)

        Returns:
            리서치 결과를 담은 ToolResult

        Raises:
            ValueError: 아웃라인이 아직 생성되지 않은 경우
        """
        _ = kwargs
        if state.outline is None:
            raise ValueError(
                "Outline must be generated before calling researcher. Call call_outliner first."
            )

        # Workflow 생성 및 실행
        workflow = self._workflow_class(model=state.model)
        researcher_state = await workflow.run(outline=state.outline)

        # 결과를 부모 상태에 병합
        state.research_results = researcher_state.section_research_results
        state.reference_documents.extend(researcher_state.reference_documents)
        state.current_phase = Phase.WRITING

        # 결과 메시지 구성
        completed = sum(1 for r in state.research_results.values() if r.research_complete)
        total = len(state.research_results)
        content = (
            f"Research completed for {completed}/{total} sections.\n"
            f"Total reference documents: {len(state.reference_documents)}"
        )

        return ToolResult(
            content=content,
            artifact={k: v.model_dump() for k, v in state.research_results.items()},
        )


class CallWriterTool(BaseTool[OrchestratorState]):
    """Writer Agent를 호출하여 최종 리포트를 작성합니다.

    아웃라인과 리서치 결과를 WriterAgent에 전달하고,
    생성된 최종 리포트를 부모 상태에 병합합니다.
    """

    name = "call_writer"
    description = (
        "Call the Writer Agent to produce the final report based on the outline "
        "and collected research. The agent will write each section, evaluate quality, "
        "and integrate everything into a cohesive report. "
        "Must be called after research is complete."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, subagent_class: type[BaseAgent[WriterState]]) -> None:
        """CallWriterTool을 초기화합니다.

        Args:
            subagent_class: 사용할 WriterAgent 클래스
        """
        self._subagent_class = subagent_class

    async def _execute(self, state: OrchestratorState, **kwargs: Any) -> ToolResult:
        """WriterAgent를 생성하고 실행하여 최종 리포트를 작성합니다.

        Args:
            state: 현재 OrchestratorState
            **kwargs: (없음)

        Returns:
            최종 리포트 결과를 담은 ToolResult

        Raises:
            ValueError: 아웃라인 또는 리서치 결과가 없는 경우
        """
        _ = kwargs
        if state.outline is None:
            raise ValueError("Outline must be generated before calling writer.")
        if not state.research_results:
            raise ValueError(
                "Research must be completed before calling writer. Call call_researcher first."
            )

        # Sub-agent 생성 및 실행
        agent = await self._subagent_class.setup(
            outline=state.outline,
            section_research=state.research_results,
            model=state.model,
        )
        await agent.run()

        # 결과를 부모 상태에 병합
        state.final_report = agent.state.final_report

        # 결과 메시지 구성
        if state.final_report:
            content = (
                f"Report '{state.final_report.title}' written successfully.\n"
                f"Sections: {len(state.final_report.sections)}\n"
                f"References: {len(state.final_report.references)}\n\n"
                f"Call final_answer to deliver the report to the user if you are satisfied with the report."
            )
        else:
            content = "Writing completed but no final report was produced."

        return ToolResult(
            content=content,
            artifact=state.final_report.model_dump() if state.final_report else None,
        )


class FinalAnswerTool(BaseTool[OrchestratorState]):
    """최종 리포트를 사용자에게 전달합니다.

    Writer Agent가 생성한 리포트를 마크다운 형식으로 사용자에게 전달하고,
    워크플로우를 완료 상태로 전환합니다.
    """

    name = "final_answer"
    description = (
        "Deliver the final report to the user. Include the complete report "
        "in markdown format. This marks the workflow as complete."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    async def _execute(self, state: OrchestratorState, **kwargs: Any) -> ToolResult:
        """최종 리포트를 전달하고 워크플로우를 완료합니다.

        Args:
            state: 현재 OrchestratorState
            **kwargs: report_markdown (str)

        Returns:
            최종 리포트를 담은 ToolResult
        """
        _ = kwargs

        if state.final_report is None:
            raise ValueError("Final report is not generated. Call call_writer first.")
        report_markdown = self._generate_report_markdown(state.final_report)
        state.current_phase = Phase.COMPLETE

        return ToolResult(
            content=report_markdown,
            artifact={"phase": Phase.COMPLETE.value},
        )

    def _generate_report_markdown(self, final_report: FinalReport) -> str:
        """최종 리포트를 마크다운 형식으로 생성합니다."""
        return f"# {final_report.title}\n\n" + "\n".join(
            f"## {s.title}\n\n{s.content}" for s in final_report.sections
        )
