"""Researcher Agent를 위한 평가 모듈.

RequiredInfoEvaluator: 섹션별 필요 정보 정의의 품질을 평가합니다.
"""

import json

from langfuse.decorators import langfuse_context
from pydantic import BaseModel, Field

from lec02_02_langfuse.router import router
from lec05_01_outliner.schemas import Outline
from lec05_02_researcher.prompts import REQUIRED_INFO_EVALUATOR_PROMPT
from lec05_02_researcher.schemas import SectionResearch


class RequiredInfoEvaluationResult(BaseModel):
    """필요 정보 정의 평가 결과."""

    passed: bool = Field(
        description="True if all required info definitions meet evaluation criteria. "
        "False if any criterion is not met.",
    )
    feedback: str = Field(
        description="If not passed, provide specific, actionable feedback. For example: "
        "'Section 2 Market Analysis: item market trends is too vague - specify growth rate, "
        "segment breakdown, regional distribution', "
        "'Section 3 Key Players: missing required info about market share data', "
        "'Section 1: only 1 required info item - need at least 3 for adequate coverage'. "
        "If passed, empty string.",
    )


class RequiredInfoEvaluator:
    """필요 정보 정의 평가자 (Loop 1).

    아웃라인의 각 섹션에 대해 정의된 필요 정보가 적절하고 충분한지
    LLM을 사용하여 평가합니다.

    다음 기준으로 평가를 수행합니다:

    - 각 필요 정보 항목이 충분히 구체적인가
    - 섹션 description을 모두 커버하는가
    - 검색 가능한 형태로 정의되었는가
    - 누락된 중요 항목이 없는가
    - 각 항목이 해당 섹션과 직접 관련되는가

    Example:
        >>> evaluator = RequiredInfoEvaluator(model="claude-4.5-sonnet")
        >>> result = await evaluator.evaluate(
        ...     outline=outline,
        ...     section_research_results=section_research_results
        ... )
        >>> if result.passed:
        ...     print("필요 정보 정의 평가 통과!")
        ... else:
        ...     print(f"평가 실패: {result.feedback}")
    """

    def __init__(self, model: str = "claude-4.5-sonnet") -> None:
        """RequiredInfoEvaluator를 초기화합니다.

        Args:
            model: 평가에 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
        """
        self.model = model

    async def evaluate(
        self,
        outline: Outline,
        section_research_results: dict[str, SectionResearch],
    ) -> RequiredInfoEvaluationResult:
        """섹션별 필요 정보 정의를 평가합니다.

        LLM을 사용하여 정의된 필요 정보가 구체적이고 충분한지,
        섹션 description을 커버하는지 평가합니다.

        Args:
            outline: 리서치 대상 아웃라인
            section_research_results: 섹션별 리서치 결과 (필요 정보 정의 포함)

        Returns:
            RequiredInfoEvaluationResult: 평가 통과 여부와 피드백
        """
        # 아웃라인을 JSON으로 직렬화
        outline_json = outline.model_dump_json(indent=2)

        # 필요 정보를 JSON으로 직렬화
        required_info_data: dict[str, list[dict[str, str]]] = {}
        for title, research in section_research_results.items():
            required_info_data[title] = [
                {"description": info.description} for info in research.required_info
            ]
        required_info_json = json.dumps(required_info_data, indent=2, ensure_ascii=False)

        # 평가 프롬프트 생성
        prompt = REQUIRED_INFO_EVALUATOR_PROMPT.format(
            outline_json=outline_json,
            required_info_json=required_info_json,
        )

        # LLM 호출 (response_format으로 구조화된 응답 수신)
        return await router.acompletion_with_response_model(
            response_model=RequiredInfoEvaluationResult,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )
