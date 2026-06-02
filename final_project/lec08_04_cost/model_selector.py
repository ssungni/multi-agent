"""작업 복잡도에 따른 모델 선택 전략.

모든 작업에 동일한 모델을 사용하는 것은 비효율적입니다.
이 모듈은 작업 유형과 복잡도에 따라 적절한 모델을 선택하는 전략을 제공합니다.

학습 포인트:
    1. 작업별 모델 매핑 (Evaluator → 경량 모델, 생성 → 고성능 모델)
    2. 복잡도 기반 동적 모델 선택
    3. 비용 추적을 통한 효과 측정

비용 비교 (예시):
    claude-4.5-sonnet: $3/1M input, $15/1M output
    gemini-3-flash:    $0.5/1M input, $3/1M output (thinking 포함)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskType(str, Enum):
    """Agent 작업 유형."""

    GENERATION = "generation"  # 아웃라인/리포트 생성 → 경량 모델
    EVALUATION = "evaluation"  # 품질 평가 → 경량 모델
    ORCHESTRATION = "orchestration"  # 워크플로우 관리 → 고성능 모델
    SEARCH_ORCHESTRATION = "search_orchestration"  # 검색 에이전트 관리 → 경량 모델
    RESULT_FILTERING = "result_filtering"  # 검색 결과 필터링 → 경량 모델


@dataclass
class ModelConfig:
    """모델 설정."""

    model: str
    max_tokens: int
    reasoning_budget: int | None = None


class ModelSelector:
    """작업 유형별 모델 선택기.

    기본 전략:
    - GENERATION → gemini-3-flash (비용 효율적 생성)
    - EVALUATION → gemini-3-flash (구조화된 판단, 대폭 비용 절감)
    - ORCHESTRATION → claude-4.5-sonnet (고품질 워크플로우 관리)
    - SEARCH_ORCHESTRATION → claude-4.5-haiku (검색 에이전트 경량 관리)
    """

    DEFAULT_MODEL_MAP: dict[TaskType, ModelConfig] = {
        TaskType.GENERATION: ModelConfig(
            model="gemini-3-flash",
            max_tokens=16000,
            reasoning_budget=1024,
        ),
        TaskType.EVALUATION: ModelConfig(
            model="gemini-3-flash",
            max_tokens=4000,
            reasoning_budget=0,
        ),
        TaskType.ORCHESTRATION: ModelConfig(
            model="claude-4.5-sonnet",
            max_tokens=8000,
            reasoning_budget=1024,
        ),
        TaskType.SEARCH_ORCHESTRATION: ModelConfig(
            model="claude-4.5-haiku",
            max_tokens=8000,
            reasoning_budget=128,
        ),
        TaskType.RESULT_FILTERING: ModelConfig(
            model="gpt-4.1-mini",
            max_tokens=4000,
            reasoning_budget=0,
        ),
    }

    def __init__(
        self,
        model_map: dict[TaskType, ModelConfig] | None = None,
    ) -> None:
        self.model_map = model_map or self.DEFAULT_MODEL_MAP

    def select(self, task_type: TaskType) -> ModelConfig:
        """작업 유형에 맞는 모델 설정을 반환합니다."""
        return self.model_map[task_type]
