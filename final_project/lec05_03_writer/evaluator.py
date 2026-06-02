"""Writer Agent를 위한 평가 모듈.

두 가지 Evaluator를 제공합니다:
- SectionEvaluator: 개별 섹션의 품질을 평가합니다 (리서치 활용도, 인용 정확성, 가독성).
- ReportEvaluator: 통합된 전체 리포트의 품질을 평가합니다 (일관성, 흐름, 중복 여부).
"""

from langfuse.decorators import langfuse_context
from pydantic import BaseModel, Field

from lec02_02_langfuse.router import router
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer.prompts import REPORT_EVALUATOR_PROMPT, SECTION_EVALUATOR_PROMPT
from lec05_03_writer.schemas import FinalReport, ReportSection


class SectionEvaluationResult(BaseModel):
    """섹션 평가 결과."""

    passed: bool = Field(
        description="True if the section meets all evaluation criteria. "
        "False if any criterion is not met.",
    )
    feedback: str = Field(
        description="If not passed, provide specific, actionable feedback. For example: "
        "'Research data about market growth rates (42% YoY) is available but not mentioned', "
        "'The outline description mentions regulatory challenges but the section does not cover this', "
        "'Paragraph 2 claims rapid growth without citing a source', "
        "'Section is only 1 paragraph - expand to at least 3 paragraphs'. "
        "If passed, empty string.",
    )


class ReportEvaluationResult(BaseModel):
    """리포트 평가 결과."""

    passed: bool = Field(
        description="True if the report meets all evaluation criteria. "
        "False if any criterion is not met.",
    )
    feedback: str = Field(
        description="If not passed, provide specific, actionable feedback. For example: "
        "'Section 2 uses casual language while Section 4 is formal - standardize tone', "
        "'Section 3 and Section 5 both discuss AI regulation - consolidate into one', "
        "'Transition from Market Analysis to Technical Trends is abrupt - add connecting paragraph', "
        "'Conclusion does not mention the key finding about market consolidation from Section 2'. "
        "If passed, empty string.",
    )


class SectionEvaluator:
    """섹션 품질 평가자 (Loop 1).

    작성된 개별 섹션의 품질을 LLM을 사용하여 평가합니다.
    다음 기준으로 평가를 수행합니다:

    - 수집된 리서치 데이터가 충분히 활용되었는가
    - 아웃라인 description에서 요구한 내용이 모두 커버되었는가
    - 출처 인용이 적절하고 정확한가
    - 문단 구성이 논리적이고 가독성이 높은가
    - 분량이 적절한가 (너무 짧거나 길지 않은가)

    Example:
        >>> evaluator = SectionEvaluator(model="claude-4.5-sonnet")
        >>> result = await evaluator.evaluate(
        ...     section=written_section,
        ...     section_description="시장 규모 현황 분석...",
        ...     section_research=section_research
        ... )
        >>> if result.passed:
        ...     print("섹션 평가 통과!")
        ... else:
        ...     print(f"평가 실패: {result.feedback}")
    """

    def __init__(self, model: str = "claude-4.5-sonnet") -> None:
        """SectionEvaluator를 초기화합니다.

        Args:
            model: 평가에 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
        """
        self.model = model

    async def evaluate(
        self,
        section: ReportSection,
        section_description: str,
        section_research: SectionResearch | None = None,
    ) -> SectionEvaluationResult:
        """작성된 섹션의 품질을 평가합니다.

        LLM을 사용하여 섹션이 리서치 데이터를 적절히 활용하고,
        아웃라인 description을 충분히 커버하며, 출처 인용이 정확하고,
        가독성이 높은지 평가합니다.

        Args:
            section: 평가할 작성된 섹션
            section_description: 아웃라인에서 가져온 섹션 설명
            section_research: 해당 섹션의 리서치 결과 (없으면 None)

        Returns:
            SectionEvaluationResult: 평가 통과 여부와 피드백
        """
        # 리서치 데이터를 요약 문자열로 생성
        research_summary = self._format_research_summary(section_research)

        # 출처 목록 포맷팅
        sources_text = "\n".join(section.sources) if section.sources else "(no sources cited)"

        # 평가 프롬프트 생성
        prompt = SECTION_EVALUATOR_PROMPT.format(
            section_title=section.title,
            section_description=section_description,
            research_summary=research_summary,
            section_content=section.content,
            section_sources=sources_text,
        )

        # LLM 호출 (response_format으로 구조화된 응답 수신)
        return await router.acompletion_with_response_model(
            response_model=SectionEvaluationResult,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )

    def _format_research_summary(self, section_research: SectionResearch | None) -> str:
        """리서치 데이터를 평가용 요약 문자열로 포맷팅합니다.

        Args:
            section_research: 섹션 리서치 결과 (없으면 None)

        Returns:
            포맷팅된 리서치 요약 문자열
        """
        if section_research is None:
            return "(no research data available)"

        parts: list[str] = []

        # 리서치 요약
        if section_research.summary:
            parts.append(f"Research summary:\n{section_research.summary}")

        # 참조 문서 (검색 결과 + 페치한 콘텐츠 통합)
        if section_research.reference_documents:
            snippets = []
            for doc in section_research.reference_documents[:5]:  # 최대 5개 (naive implementation)
                snippets.append(f"- [{doc.title}]({doc.url}): {doc.snippet}")
                if doc.content:
                    truncated = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
                    snippets.append(f"  Content: {truncated}")
            parts.append("Reference documents:\n" + "\n".join(snippets))

        return "\n\n".join(parts) if parts else "(no research data available)"


class ReportEvaluator:
    """리포트 품질 평가자 (Loop 2).

    통합된 전체 리포트의 품질을 LLM을 사용하여 평가합니다.
    다음 기준으로 평가를 수행합니다:

    - 섹션 간 문체 일관성이 유지되는가
    - 전체적인 논리적 흐름이 자연스러운가
    - 섹션 간 연결이 매끄러운가
    - 서론이 전체 내용을 적절히 소개하는가
    - 결론이 본문 내용을 잘 요약하는가
    - 중복되는 내용이 없는가
    - 전체 톤앤매너가 일관되는가

    Example:
        >>> evaluator = ReportEvaluator(model="claude-4.5-sonnet")
        >>> result = await evaluator.evaluate(final_report)
        >>> if result.passed:
        ...     print("리포트 평가 통과!")
        ... else:
        ...     print(f"평가 실패: {result.feedback}")
    """

    def __init__(self, model: str = "claude-4.5-sonnet") -> None:
        """ReportEvaluator를 초기화합니다.

        Args:
            model: 평가에 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
        """
        self.model = model

    async def evaluate(
        self,
        report: FinalReport,
    ) -> ReportEvaluationResult:
        """통합된 리포트의 전체 품질을 평가합니다.

        LLM을 사용하여 리포트의 문체 일관성, 논리적 흐름, 섹션 간 연결,
        서론/결론 품질, 중복 여부, 톤 일관성을 평가합니다.

        Args:
            report: 평가할 최종 리포트

        Returns:
            ReportEvaluationResult: 평가 통과 여부와 피드백
        """
        # 리포트 전문을 텍스트로 구성
        report_content = self._format_report_content(report)

        # 평가 프롬프트 생성
        prompt = REPORT_EVALUATOR_PROMPT.format(
            report_title=report.title,
            report_content=report_content,
        )

        # LLM 호출 (response_format으로 구조화된 응답 수신)
        return await router.acompletion_with_response_model(
            response_model=ReportEvaluationResult,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )

    def _format_report_content(self, report: FinalReport) -> str:
        """리포트 전문을 평가용 텍스트로 포맷팅합니다.

        Args:
            report: 최종 리포트

        Returns:
            포맷팅된 리포트 전문 문자열
        """
        parts: list[str] = [f"# {report.title}\n"]

        for section in report.sections:
            parts.append(f"## {section.title}\n")
            parts.append(section.content)
            parts.append("")  # 빈 줄

        if report.references:
            parts.append("## References\n")
            for i, ref in enumerate(report.references, 1):
                parts.append(f"{i}. {ref}")

        return "\n".join(parts)
