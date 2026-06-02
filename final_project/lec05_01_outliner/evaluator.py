"""Outliner Agent를 위한 평가 모듈.

OutlineEvaluator는 생성된 아웃라인의 품질을 LLM 기반으로 평가합니다.
아웃라인이 적절한 구조, 충분한 구체성, 논리적 흐름을 갖추었는지 검증합니다.
"""

from langfuse.decorators import langfuse_context, observe
from pydantic import BaseModel, Field

from lec02_02_langfuse.router import router
from lec05_01_outliner.prompts import EVALUATOR_PROMPT
from lec05_01_outliner.schemas import Outline


class EvaluationResult(BaseModel):
    """아웃라인 평가 결과."""

    passed: bool = Field(
        description="True if the outline meets all evaluation criteria. "
        "False if any criterion is not met.",
    )
    feedback: str = Field(
        description="If not passed, provide specific, actionable feedback. For example: "
        "'Section 2 and Section 4 have overlapping content - merge or differentiate', "
        "'Section 3 description is too vague - specify concrete topics', "
        "'Missing coverage of regulatory considerations', "
        "'Only 2 main sections - expand to at least 3-4'. "
        "If passed, empty string.",
    )


class OutlineEvaluator:
    """아웃라인 품질 평가자.

    생성된 아웃라인을 LLM을 사용하여 평가합니다.
    다음 기준으로 평가를 수행합니다:

    - 섹션 개수가 적정 범위 내인가 (3~7개)
    - 각 섹션의 description이 충분히 구체적인가
    - 섹션 간 내용 중복이 없는가
    - 논리적 흐름이 자연스러운가 (서론 → 본론 → 결론)
    - 입력 주제와의 관련성이 높은가

    Example:
        >>> evaluator = OutlineEvaluator(model="claude-4.5-sonnet")
        >>> result = await evaluator.evaluate(
        ...     topic="Generative AI market trends in 2024",
        ...     outline=outline
        ... )
        >>> if result.passed:
        ...     print("아웃라인 평가 통과!")
        ... else:
        ...     print(f"평가 실패: {result.feedback}")
    """

    def __init__(self, model: str = "claude-4.5-sonnet") -> None:
        """OutlineEvaluator를 초기화합니다.

        Args:
            model: 평가에 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
        """
        self.model = model

    @observe(name="outline_evaluate", capture_input=True, capture_output=True)
    async def evaluate(self, topic: str, outline: Outline) -> EvaluationResult:
        """아웃라인의 품질을 평가합니다.

        LLM을 사용하여 아웃라인이 주제에 적합하고 충분히 구체적이며
        논리적으로 잘 구성되어 있는지 평가합니다.

        Args:
            topic: 사용자가 입력한 원본 주제
            outline: 평가할 아웃라인 객체

        Returns:
            EvaluationResult: 평가 통과 여부와 피드백을 포함한 결과

        Example:
            >>> evaluator = OutlineEvaluator()
            >>> outline = Outline(
            ...     title="AI Market Trends",
            ...     sections=[
            ...         OutlineSection(
            ...             title="Introduction",
            ...             description="Overview of AI market in 2024",
            ...             subsections=[]
            ...         )
            ...     ]
            ... )
            >>> result = await evaluator.evaluate("AI trends", outline)
            >>> result.passed
            False
            >>> "2 main sections" in result.feedback
            True
        """
        # 아웃라인을 JSON으로 직렬화
        outline_json = outline.model_dump_json(indent=2)

        # 평가 프롬프트 생성
        prompt = EVALUATOR_PROMPT.format(
            topic=topic,
            outline_json=outline_json,
        )

        # LLM 호출 (response_format으로 구조화된 응답 수신)
        return await router.acompletion_with_response_model(
            response_model=EvaluationResult,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )
