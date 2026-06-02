"""Outliner Agent 도구 모듈.

아웃라인 생성 및 최종화를 수행하는 도구들을 제공합니다.
내부 LLM 호출과 평가 루프를 통해 품질이 검증된 아웃라인을 생성합니다.
"""

from typing import Any

from langfuse.decorators import langfuse_context

from lec02_02_langfuse.router import router
from lec04_01_base_agent.tool import BaseTool, ToolResult
from lec04_02_tools.schemas import ReferenceDocument
from lec05_01_outliner.evaluator import OutlineEvaluator
from lec05_01_outliner.prompts import OUTLINE_GENERATION_PROMPT
from lec05_01_outliner.schemas import Outline
from lec05_01_outliner.state import OutlinerState


class GenerateOutlineTool(BaseTool[OutlinerState]):
    """수집된 검색 결과로부터 구조화된 아웃라인을 생성합니다.

    내부적으로 LLM을 호출하여 아웃라인을 생성하고,
    OutlineEvaluator로 평가하여 품질 기준을 충족할 때까지 루프를 돕니다.
    """

    name = "generate_outline"
    description = (
        "Generate a structured outline from collected search results. "
        "Call this after gathering sufficient search results to cover the topic. "
        "The tool internally generates the outline using an LLM and evaluates it, "
        "retrying until quality criteria are met."
    )
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic of the report",
            },
        },
        "required": ["topic"],
        "additionalProperties": False,
    }

    def __init__(self, model: str = "claude-4.5-sonnet", max_retries: int = 3):
        self.model = model
        self.max_retries = max_retries
        self.evaluator = OutlineEvaluator(model=model)

    async def _execute(self, state: OutlinerState, **kwargs: Any) -> ToolResult:
        """아웃라인을 내부 LLM으로 생성하고 평가 루프를 수행합니다.

        Args:
            state: 현재 OutlinerState
            **kwargs: topic (str)

        Returns:
            평가를 통과한 아웃라인을 담은 ToolResult
        """
        topic: str = kwargs.get("topic", "")
        if not topic:
            raise ValueError("Topic is required")

        reference_documents = state.reference_documents

        # 1) LLM으로 outline 생성
        if not reference_documents:
            raise ValueError("Search results are required")

        outline = await self._generate_outline(topic, reference_documents)

        # 2) 평가 루프
        eval_result = await self.evaluator.evaluate(topic, outline)
        for _ in range(self.max_retries):
            if eval_result.passed:
                break

            feedback = eval_result.feedback or ""
            if not feedback:
                feedback = "No feedback provided, but the outline is not passed."

            outline = await self._generate_outline(topic, reference_documents, feedback=feedback)
            eval_result = await self.evaluator.evaluate(topic, outline)

        # 3) state 업데이트
        state.outline = outline
        state.evaluation_passed = eval_result.passed
        state.evaluation_feedback = eval_result.feedback if not eval_result.passed else None

        return ToolResult(content=self._format_outline(outline), artifact=outline)

    async def _generate_outline(
        self,
        topic: str,
        reference_documents: list[ReferenceDocument],
        feedback: str | None = None,
    ) -> Outline:
        """LLM을 호출하여 Outline 스키마로 아웃라인을 생성합니다."""
        # 검색 결과를 텍스트로 변환
        search_context = "\n\n".join(
            f"[{i + 1}] {r.title}\n{r.content or r.snippet}"
            for i, r in enumerate(reference_documents)
        )

        prompt = OUTLINE_GENERATION_PROMPT.format(
            topic=topic,
            search_results=search_context,
            feedback_section=(
                f"\n\n## Previous Evaluation Feedback\nAddress the following feedback:\n{feedback}"
                if feedback
                else ""
            ),
        )

        return await router.acompletion_with_response_model(
            response_model=Outline,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )

    def _format_outline(self, outline: Outline) -> str:
        """아웃라인을 포맷팅합니다."""
        lines = [f"Generated outline: {outline.title}\n"]

        for i, section in enumerate(outline.sections, 1):
            lines.append(f"{i}. {section.title}")
            lines.append(f"   Description: {section.description}")

            if section.subsections:
                lines.append("   Subsections:")
                for subsection in section.subsections:
                    lines.append(f"   - {subsection}")

            lines.append("")  # 빈 줄 추가

        return "\n".join(lines)
