"""Score 기반 Evaluator — score에서 passed를 도출하는 패턴.

lec05의 기존 Evaluator는 LLM이 passed(bool) + feedback(str)을 직접 판단합니다.
이 모듈은 LLM에게 score(float) + feedback(str)만 요청한 뒤,
score >= _PASS_THRESHOLD 로 passed를 도출하여 기존 Result 타입으로 반환합니다.

학습 포인트:
    - LLM이 passed와 score를 동시에 판단하면 불일치 위험 (lec08_03 참고)
    - score만 받아 passed를 도출하면 일관성 보장 + soft pass 자동 적용
    - evaluate()의 반환 타입이 기존과 동일하므로 Tool 내부 평가 루프 수정 불필요

Added: score-based passed derivation for cost optimization (lec08_04_cost)
"""

from __future__ import annotations

import json

from langfuse.decorators import langfuse_context
from pydantic import BaseModel, Field

from lec02_02_langfuse.router import router
from lec05_01_outliner.evaluator import EvaluationResult, OutlineEvaluator
from lec05_01_outliner.prompts import EVALUATOR_PROMPT
from lec05_01_outliner.schemas import Outline
from lec05_02_researcher.evaluator import (
    RequiredInfoEvaluationResult,
    RequiredInfoEvaluator,
)
from lec05_02_researcher.prompts import REQUIRED_INFO_EVALUATOR_PROMPT
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer.evaluator import (
    ReportEvaluationResult,
    ReportEvaluator,
    SectionEvaluationResult,
    SectionEvaluator,
)
from lec05_03_writer.prompts import REPORT_EVALUATOR_PROMPT, SECTION_EVALUATOR_PROMPT
from lec05_03_writer.schemas import FinalReport, ReportSection

# score >= 0.7 이면 passed=True
_PASS_THRESHOLD = 0.7

_SCORE_DESCRIPTION = (
    "Quality score from 0.0 to 1.0. "
    "0.0 = completely inadequate, 0.5 = partially meets criteria, "
    "0.7 = mostly good with minor issues, 1.0 = excellent."
)


class _ScoredEvalResponse(BaseModel):
    """LLM 응답 모델 — score + feedback만 반환 (passed는 score에서 도출)."""

    score: float = Field(ge=0.0, le=1.0, description=_SCORE_DESCRIPTION)
    feedback: str = Field(
        description="Specific, actionable feedback for improvement. "
        "Empty string if quality is excellent.",
    )


# =============================================================================
# Score 기반 Evaluator — 기존 Evaluator 상속, evaluate() 반환 타입 유지
# =============================================================================


class ScoredOutlineEvaluator(OutlineEvaluator):
    """score 기반 passed 도출 OutlineEvaluator (lec08_03 패턴)."""

    async def evaluate(self, topic: str, outline: Outline) -> EvaluationResult:
        prompt = EVALUATOR_PROMPT.format(
            topic=topic,
            outline_json=outline.model_dump_json(indent=2),
        )
        result = await router.acompletion_with_response_model(
            response_model=_ScoredEvalResponse,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )
        return EvaluationResult(
            passed=result.score >= _PASS_THRESHOLD,
            feedback=result.feedback if result.score < _PASS_THRESHOLD else "",
        )


class ScoredRequiredInfoEvaluator(RequiredInfoEvaluator):
    """score 기반 passed 도출 RequiredInfoEvaluator."""

    async def evaluate(
        self,
        outline: Outline,
        section_research_results: dict[str, SectionResearch],
    ) -> RequiredInfoEvaluationResult:
        outline_json = outline.model_dump_json(indent=2)

        required_info_data: dict[str, list[dict[str, str]]] = {}
        for title, research in section_research_results.items():
            required_info_data[title] = [
                {"description": info.description} for info in research.required_info
            ]
        required_info_json = json.dumps(required_info_data, indent=2, ensure_ascii=False)

        prompt = REQUIRED_INFO_EVALUATOR_PROMPT.format(
            outline_json=outline_json,
            required_info_json=required_info_json,
        )
        result = await router.acompletion_with_response_model(
            response_model=_ScoredEvalResponse,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )
        return RequiredInfoEvaluationResult(
            passed=result.score >= _PASS_THRESHOLD,
            feedback=result.feedback if result.score < _PASS_THRESHOLD else "",
        )


class ScoredSectionEvaluator(SectionEvaluator):
    """score 기반 passed 도출 SectionEvaluator."""

    async def evaluate(
        self,
        section: ReportSection,
        section_description: str,
        section_research: SectionResearch | None = None,
    ) -> SectionEvaluationResult:
        research_summary = self._format_research_summary(section_research)
        sources_text = "\n".join(section.sources) if section.sources else "(no sources cited)"
        prompt = SECTION_EVALUATOR_PROMPT.format(
            section_title=section.title,
            section_description=section_description,
            research_summary=research_summary,
            section_content=section.content,
            section_sources=sources_text,
        )
        result = await router.acompletion_with_response_model(
            response_model=_ScoredEvalResponse,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )
        return SectionEvaluationResult(
            passed=result.score >= _PASS_THRESHOLD,
            feedback=result.feedback if result.score < _PASS_THRESHOLD else "",
        )


class ScoredReportEvaluator(ReportEvaluator):
    """score 기반 passed 도출 ReportEvaluator."""

    async def evaluate(self, report: FinalReport) -> ReportEvaluationResult:
        report_content = self._format_report_content(report)
        prompt = REPORT_EVALUATOR_PROMPT.format(
            report_title=report.title,
            report_content=report_content,
        )
        result = await router.acompletion_with_response_model(
            response_model=_ScoredEvalResponse,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )
        return ReportEvaluationResult(
            passed=result.score >= _PASS_THRESHOLD,
            feedback=result.feedback if result.score < _PASS_THRESHOLD else "",
        )
