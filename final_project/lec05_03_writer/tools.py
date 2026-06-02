"""Writer Agent 도구 모듈.

섹션 작성 및 리포트 최종화를 수행하는 도구들을 제공합니다.
WriteSectionTool은 별도의 LLM 호출로 섹션을 작성하고 SectionEvaluator로 품질을 검증하며,
PolishReportTool은 상태에 저장된 섹션들을 통합하고 ReportEvaluator로 품질을 검증합니다.
각 도구는 내부에서 평가 루프를 수행합니다.
"""

import logging
from typing import Any

from langfuse.decorators import langfuse_context
from pydantic import BaseModel, Field

from lec02_02_langfuse.router import router
from lec04_01_base_agent.tool import BaseTool, ToolResult
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer.evaluator import ReportEvaluator, SectionEvaluator
from lec05_03_writer.prompts import REPORT_POLISH_PROMPT, SECTION_WRITER_PROMPT
from lec05_03_writer.schemas import FinalReport, ReportSection
from lec05_03_writer.state import WriterState

logger = logging.getLogger(__name__)


class WrittenSectionOutput(BaseModel):
    """섹션 작성 LLM 호출의 응답 모델."""

    content: str = Field(
        description="Section body content in markdown format. Incorporate research data naturally "
        "with proper source citations (URLs) for factual claims. Use clear paragraph structure "
        "with logical flow. Aim for 3-6 paragraphs of substantive depth.",
    )
    sources: list[str] = Field(
        default=[],
        description="List of source URLs cited in the content for factual claims and data points.",
    )


class WriteSectionTool(BaseTool[WriterState]):
    """별도의 LLM 호출로 리포트 섹션을 작성합니다.

    내부적으로 LLM을 호출하여 섹션을 작성하고,
    SectionEvaluator로 평가하여 품질 기준을 충족할 때까지 루프를 돕니다.
    """

    name = "write_section"
    description = (
        "Write a report section by delegating to a separate LLM call with the relevant "
        "research data. Provide only the section title; the tool will independently generate "
        "the content. The tool internally evaluates the quality and retries until criteria are met."
    )
    parameters = {
        "type": "object",
        "properties": {
            "section_title": {
                "type": "string",
                "description": "Title of the section to write (must match an outline section title)",
            },
        },
        "required": ["section_title"],
        "additionalProperties": False,
    }

    def __init__(self, model: str = "claude-4.5-sonnet", max_retries: int = 3):
        self.model = model
        self.max_retries = max_retries
        self.evaluator = SectionEvaluator(model=model)

    async def _execute(self, state: WriterState, **kwargs: Any) -> ToolResult:
        """섹션을 내부 LLM으로 작성하고 평가 루프를 수행합니다.

        Args:
            state: 현재 WriterState
            **kwargs: section_title (str)

        Returns:
            평가를 통과한 섹션을 담은 ToolResult

        Raises:
            ValueError: section_title이 제공되지 않았거나 아웃라인에 없을 때
        """
        section_title: str = kwargs.get("section_title", "")

        if not section_title:
            raise ValueError("section_title is required")

        # 아웃라인에서 섹션 description 찾기
        section_description = ""
        if state.outline:
            for outline_section in state.outline.sections:
                if outline_section.title == section_title:
                    section_description = outline_section.description
                    break

        if not section_description:
            raise ValueError(
                f"Section '{section_title}' not found in outline. "
                f"Available sections: {[s.title for s in state.outline.sections] if state.outline else []}"
            )

        # 리서치 데이터 가져오기
        section_research = state.section_research.get(section_title)
        research_data = self._format_research_data(section_research)

        # 1) LLM으로 섹션 작성
        section = await self._generate_section(
            section_title,
            section_description,
            research_data,
            state.model,
        )

        # 2) 평가 루프
        eval_result = await self.evaluator.evaluate(
            section=section,
            section_description=section_description,
            section_research=section_research,
        )
        for _ in range(self.max_retries):
            if eval_result.passed:
                break

            feedback = eval_result.feedback or "No feedback provided, but the section did not pass."
            logger.info("Section '%s' evaluation failed: %s", section_title, feedback)

            section = await self._generate_section(
                section_title,
                section_description,
                research_data,
                state.model,
                feedback=feedback,
            )
            eval_result = await self.evaluator.evaluate(
                section=section,
                section_description=section_description,
                section_research=section_research,
            )

        # 3) state 업데이트
        state.written_sections[section_title] = section
        if eval_result.passed:
            state.passed_sections.add(section_title)
            state.section_evaluation_feedback.pop(section_title, None)
        else:
            state.section_evaluation_feedback[section_title] = eval_result.feedback

        # 모든 섹션이 통과했는지 확인
        if state.outline:
            all_titles = {s.title for s in state.outline.sections}
            state.sections_evaluation_passed = all_titles <= state.passed_sections

        # 결과 포맷팅
        result_content = self._format_section_result(section)

        return ToolResult(content=result_content, artifact=section)

    async def _generate_section(
        self,
        section_title: str,
        section_description: str,
        research_data: str,
        model: str,
        feedback: str | None = None,
    ) -> ReportSection:
        """LLM을 호출하여 섹션을 작성합니다."""
        revision_context = ""
        if feedback:
            revision_context = (
                f"\n## Revision Required\n\n"
                f"Your previous attempt was evaluated and needs improvement.\n\n"
                f"### Evaluation Feedback (address these issues)\n{feedback}\n"
            )

        prompt = SECTION_WRITER_PROMPT.format(
            section_title=section_title,
            section_description=section_description,
            research_data=research_data,
            revision_context=revision_context,
        )

        output = await router.acompletion_with_response_model(
            response_model=WrittenSectionOutput,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )

        return ReportSection(
            title=section_title,
            content=output.content,
            sources=output.sources,
        )

    def _format_research_data(self, section_research: SectionResearch | None) -> str:
        """리서치 데이터를 프롬프트용 문자열로 포맷팅합니다.

        Args:
            section_research: 섹션 리서치 결과 (없으면 None)

        Returns:
            포맷팅된 리서치 데이터 문자열
        """
        if section_research is None:
            return "(no research data available)"

        parts: list[str] = []

        # 리서치 요약
        if section_research.summary:
            parts.append(f"### Research Summary\n{section_research.summary}")

        # 참조 문서 (검색 결과 + 페치한 콘텐츠 통합)
        if section_research.reference_documents:
            docs = []
            for doc in section_research.reference_documents:
                docs.append(f"- [{doc.title}]({doc.url}): {doc.content or doc.snippet}")
                if doc.content:
                    truncated = (
                        doc.content[:2000] + "..." if len(doc.content) > 2000 else doc.content
                    )
                    docs.append(f"  Content:\n{truncated}")
            parts.append("### Reference Documents\n" + "\n".join(docs))

        return "\n\n".join(parts) if parts else "(no research data available)"

    def _format_section_result(self, section: ReportSection) -> str:
        """작성된 섹션 결과를 포맷팅합니다.

        Args:
            section: 작성된 ReportSection

        Returns:
            포맷팅된 섹션 결과 문자열
        """
        lines = [
            f"Section '{section.title}' written successfully.",
            f"Content length: {len(section.content)} characters",
            f"Sources cited: {len(section.sources)}",
        ]

        if section.sources:
            lines.append("Source URLs:")
            for url in section.sources:
                lines.append(f"  - {url}")

        return "\n".join(lines)


class IntegratedSectionOutput(BaseModel):
    """최종 리포트의 통합된 섹션 응답 모델."""

    title: str = Field(
        description="Section title. Must match one of the original section titles.",
    )
    content: str = Field(
        description="Section content rewritten for style consistency with other sections, "
        "smooth transitions, and no content duplication. Preserve all source citations "
        "and factual accuracy from the original.",
    )
    sources: list[str] = Field(
        default=[],
        description="Source URLs cited in this section. Preserve all citations from the original.",
    )


class FinalReportOutput(BaseModel):
    """최종 리포트 통합 LLM 호출의 응답 모델."""

    sections: list[IntegratedSectionOutput] = Field(
        description="All report sections integrated for consistent style, smooth transitions, "
        "and no content duplication. Maintain the original section order.",
    )
    references: list[str] = Field(
        default=[],
        description="Consolidated list of all unique source URLs from all sections, "
        "in order of first appearance.",
    )


class PolishReportTool(BaseTool[WriterState]):
    """별도의 LLM 호출로 작성된 섹션들을 일관성 있는 최종 리포트로 통합합니다.

    내부적으로 LLM을 호출하여 리포트를 통합하고,
    ReportEvaluator로 평가하여 품질 기준을 충족할 때까지 루프를 돕니다.
    """

    name = "polish_report"
    description = (
        "Integrate all written sections into a cohesive final report via a separate LLM call. "
        "The tool takes written sections and produces a unified report with consistent style "
        "and smooth transitions. The tool internally evaluates the quality and retries "
        "until criteria are met."
    )
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the final report",
            },
        },
        "required": ["title"],
        "additionalProperties": False,
    }

    def __init__(self, model: str = "claude-4.5-sonnet", max_retries: int = 3):
        self.model = model
        self.max_retries = max_retries
        self.evaluator = ReportEvaluator(model=model)

    async def _execute(self, state: WriterState, **kwargs: Any) -> ToolResult:
        """작성된 섹션들을 내부 LLM으로 통합하고 평가 루프를 수행합니다.

        Args:
            state: 현재 WriterState
            **kwargs: title (str)

        Returns:
            평가를 통과한 최종 리포트를 담은 ToolResult

        Raises:
            ValueError: title이 제공되지 않았거나 작성된 섹션이 없을 때
        """
        title: str = kwargs.get("title", "")

        if not title:
            raise ValueError("title is required")

        if not state.written_sections:
            raise ValueError("No written sections available. Write sections first.")

        # 아웃라인 순서대로 섹션 수집
        sections: list[ReportSection] = []
        if state.outline:
            for outline_section in state.outline.sections:
                if outline_section.title in state.written_sections:
                    sections.append(state.written_sections[outline_section.title])
        else:
            sections = list(state.written_sections.values())

        # 섹션 콘텐츠를 프롬프트용 문자열로 포맷팅
        sections_content = self._format_sections_for_prompt(sections)

        # 1) LLM으로 리포트 통합
        final_report = await self._generate_report(title, sections_content, state.model)

        # 2) 평가 루프
        eval_result = await self.evaluator.evaluate(report=final_report)
        for _ in range(self.max_retries):
            if eval_result.passed:
                break

            feedback = eval_result.feedback or "No feedback provided, but the report did not pass."
            logger.info("Report evaluation failed: %s", feedback)

            final_report = await self._generate_report(
                title,
                sections_content,
                state.model,
                feedback=feedback,
            )
            eval_result = await self.evaluator.evaluate(report=final_report)

        # 3) state 업데이트
        state.final_report = final_report
        state.report_evaluation_passed = eval_result.passed
        state.report_evaluation_feedback = eval_result.feedback if not eval_result.passed else None

        # 결과 포맷팅
        result_content = self._format_report_result(final_report)

        return ToolResult(content=result_content, artifact=final_report)

    async def _generate_report(
        self,
        title: str,
        sections_content: str,
        model: str,
        feedback: str | None = None,
    ) -> FinalReport:
        """LLM을 호출하여 최종 리포트를 생성합니다."""
        revision_context = ""
        if feedback:
            revision_context = (
                f"\n## Revision Required\n\n"
                f"The previous integrated report was evaluated and needs improvement.\n\n"
                f"### Evaluation Feedback (address these issues)\n{feedback}\n"
            )

        prompt = REPORT_POLISH_PROMPT.format(
            report_title=title,
            sections_content=sections_content,
            revision_context=revision_context,
        )

        output = await router.acompletion_with_response_model(
            response_model=FinalReportOutput,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )

        integrated_sections = [
            ReportSection(
                title=s.title,
                content=s.content,
                sources=s.sources,
            )
            for s in output.sections
        ]
        return FinalReport(
            title=title,
            sections=integrated_sections,
            references=output.references,
        )

    def _format_sections_for_prompt(self, sections: list[ReportSection]) -> str:
        """섹션들을 프롬프트용 문자열로 포맷팅합니다.

        Args:
            sections: 작성된 섹션 목록

        Returns:
            포맷팅된 섹션 문자열
        """
        parts: list[str] = []
        for i, section in enumerate(sections, 1):
            sources_text = ", ".join(section.sources) if section.sources else "(none)"
            parts.append(
                f"### {i}. {section.title}\n\n{section.content}\n\nSources: {sources_text}"
            )
        return "\n\n---\n\n".join(parts)

    def _format_report_result(self, report: FinalReport) -> str:
        """최종 리포트 결과를 포맷팅합니다.

        Args:
            report: 생성된 FinalReport

        Returns:
            포맷팅된 리포트 결과 문자열
        """
        lines = [
            f"Report '{report.title}' finalized.",
            f"Total sections: {len(report.sections)}",
            f"Total references: {len(report.references)}",
            "",
            "Sections:",
        ]

        for i, section in enumerate(report.sections, 1):
            lines.append(f"  {i}. {section.title} ({len(section.content)} chars)")

        return "\n".join(lines)
