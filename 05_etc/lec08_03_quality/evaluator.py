"""개선된 Evaluator - 기존 대비 품질 향상 시연.

기존 OutlineEvaluator를 확장하여:
1. 더 구체적인 평가 기준 (rubric 기반)
2. 점수화된 평가 (기준별 1-5점)
3. 단계별 피드백 (우선순위 정렬)
4. 개선 제안의 구체성 강화

학습 포인트:
    - 기존 passed/feedback만 반환하던 EvaluationResult 대신,
      기준별 점수(CriterionScore)와 우선순위 피드백을 포함하는
      DetailedEvaluationResult를 반환합니다.
    - ``feedback`` property를 통해 기존 EvaluationResult와의
      하위 호환성을 유지합니다.

사용 예시::

    >>> from lec08_03_quality.evaluator import EnhancedOutlineEvaluator
    >>> evaluator = EnhancedOutlineEvaluator(model="claude-4.5-sonnet")
    >>> result = await evaluator.evaluate(topic="AI Trends", outline=outline)
    >>> result.overall_score
    0.72
    >>> result.criteria_scores["coverage"].score
    4
    >>> result.feedback  # 하위 호환 property
    '1. [coverage] Add a section on ...'
"""

from __future__ import annotations

from langfuse.decorators import langfuse_context
from pydantic import BaseModel, Field, computed_field

from lec02_02_langfuse.router import router
from lec05_01_outliner.evaluator import EvaluationResult, OutlineEvaluator
from lec05_01_outliner.schemas import Outline
from lec08_03_quality.prompts import IMPROVED_EVALUATOR_PROMPT

# ---------------------------------------------------------------------------
# 평가 기준별 점수 모델
# ---------------------------------------------------------------------------


class CriterionScore(BaseModel):
    """개별 평가 기준 점수.

    각 평가 기준(Coverage, Structure 등)에 대한 점수, 사유, 개선 제안을
    구조화합니다.

    Attributes:
        score: 1-5 점수. 1=매우 미흡, 2=미흡, 3=보통, 4=우수, 5=매우 우수
        reason: 해당 점수를 부여한 구체적 사유
    """

    score: int = Field(
        ge=1,  # greater than or equal to 1 (1 이상)
        le=5,  # less than or equal to 5 (5 이하)
        description="Score from 1 to 5. 1=very poor, 2=poor, 3=average, 4=good, 5=excellent.",
    )
    reason: str = Field(
        description="Specific reason for the assigned score. "
        "Reference concrete elements from the outline.",
    )


# ---------------------------------------------------------------------------
# 상세 평가 결과 모델
# ---------------------------------------------------------------------------


class DetailedEvaluationResult(BaseModel):
    """상세 평가 결과 - 기준별 점수와 피드백 포함.

    기존 EvaluationResult(passed, feedback)를 확장하여 기준별 점수,
    우선순위 피드백, 구체적 개선 예시를 제공합니다.

    ``feedback`` computed property를 통해 기존 EvaluationResult 인터페이스와
    하위 호환성을 유지합니다.

    Attributes:
        criteria_scores: 기준별 CriterionScore 딕셔너리.
            키는 기준명(coverage, structure 등), 값은 CriterionScore.
        prioritized_feedback: 우선순위순 피드백 목록.
            가장 시급한 개선 사항이 먼저 옵니다.
    """

    criteria_scores: dict[str, CriterionScore] = Field(
        description="Per-criterion scores. Keys are criterion names "
        "(e.g., 'coverage', 'structure'), values are CriterionScore.",
    )  # 평균 3.5점 이상이면, passed=True
    prioritized_feedback: list[str] = Field(
        description="Feedback items ordered by priority (most urgent first). "
        "Each item is a specific, actionable improvement suggestion.",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def feedback(self) -> str:
        """하위 호환용 feedback 문자열.

        기존 EvaluationResult.feedback와 동일한 인터페이스를 제공합니다.
        prioritized_feedback 목록을 번호가 매겨진 문자열로 결합하여 반환합니다.

        Returns:
            우선순위 피드백을 결합한 문자열. 피드백이 없으면 빈 문자열.
        """
        if not self.prioritized_feedback:
            return ""
        return "\n".join(f"{i}. {item}" for i, item in enumerate(self.prioritized_feedback, 1))


# ---------------------------------------------------------------------------
# 강화된 아웃라인 평가자
# ---------------------------------------------------------------------------


class EnhancedOutlineEvaluator(OutlineEvaluator):
    """강화된 아웃라인 평가자.

    기존 OutlineEvaluator를 확장하여:
    - Rubric 기반의 세분화된 평가
    - 기준별 점수와 구체적 피드백
    - 우선순위가 매겨진 개선 제안

    기존 OutlineEvaluator와의 차이점:
        - evaluate()가 EvaluationResult 대신 DetailedEvaluationResult를 반환
        - 6개 기준 각각에 대해 1-5점 점수, 사유, 개선 제안 제공
        - 우선순위가 매겨진 피드백과 구체적 개선 예시 포함

    Example::

        >>> evaluator = EnhancedOutlineEvaluator(model="claude-4.5-sonnet")
        >>> result = await evaluator.evaluate(
        ...     topic="Generative AI market trends in 2024",
        ...     outline=outline,
        ... )
        >>> passed = (sum(score.score for score in result.criteria_scores.values()) / len(result.criteria_scores)) >= 3.5
        >>> result.feedback  # 하위 호환 property
        '1. [specificity] Add concrete data points...\\n2. ...'
    """

    async def evaluate(  # type: ignore[override]
        self, topic: str, outline: Outline
    ) -> EvaluationResult:
        """Rubric 기반 상세 평가를 수행합니다.

        LLM을 사용하여 6개 기준(coverage, structure, specificity, balance,
        relevance, uniqueness)에 대해 각각 1-5점 점수를 부여하고,
        우선순위 피드백과 구체적 개선 예시를 생성합니다.

        Args:
            topic: 사용자가 입력한 원본 주제
            outline: 평가할 아웃라인 객체

        Returns:
            EvaluationResult: 통과 결과, 피드백
        """
        outline_json = outline.model_dump_json(indent=2)

        prompt = IMPROVED_EVALUATOR_PROMPT.format(
            topic=topic,
            outline_json=outline_json,
        )

        result = await router.acompletion_with_response_model(
            response_model=DetailedEvaluationResult,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )

        averaged_score = sum(score.score for score in result.criteria_scores.values()) / len(
            result.criteria_scores
        )
        return EvaluationResult(
            passed=averaged_score >= 3.5,
            feedback=result.feedback,
        )
