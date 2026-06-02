"""Outliner Agent 구현.

주어진 주제로부터 구조화된 아웃라인을 생성하는 OutlinerAgent를 정의합니다.
웹 검색을 통해 정보를 수집하고, GenerateOutlineTool 내부의 LLM 생성+평가 루프를 통해 품질을 검증합니다.
"""

from langfuse.decorators import observe
from typing_extensions import Self

from lec04_01_base_agent.base import BaseAgent
from lec04_02_tools.fetch import FetchTool
from lec04_02_tools.search import SearchTool
from lec05_01_outliner.prompts import OUTLINER_SYSTEM_PROMPT
from lec05_01_outliner.state import OutlinerState
from lec05_01_outliner.tools import GenerateOutlineTool


class OutlinerAgent(BaseAgent[OutlinerState]):
    """주어진 주제에 대해 구조화된 아웃라인을 생성하는 에이전트.

    이 에이전트는 다음 단계를 수행합니다:

    1. **쿼리 확장 및 웹 검색**: 사용자 주제를 다양한 검색 쿼리로 확장하여 웹 검색 수행
    2. **정보 수집**: 검색 스니펫을 수집하고, 필요시 웹페이지 전문 추출
    3. **아웃라인 생성 및 평가**: GenerateOutlineTool 내부에서 LLM이 아웃라인을 생성하고
       OutlineEvaluator가 품질을 검증하는 루프를 자동으로 수행

    에이전트는 매니저 역할만 수행합니다:
    - 검색 전략을 결정하고 충분한 정보를 수집
    - generate_outline 도구를 호출하여 아웃라인 생성을 위임
    - 도구 내부에서 생성+평가 루프가 자동으로 수행됨

    Attributes:
        state: 에이전트의 실행 상태 (OutlinerState)
        tools: 사용 가능한 도구 목록 (SearchTool, FetchTool, GenerateOutlineTool)
        max_iterations: 최대 반복 횟수
        model: 사용할 LLM 모델 이름
        stream: 스트리밍 모드 사용 여부

    Example:
        >>> agent = await OutlinerAgent.setup(
        ...     topic="Generative AI market trends in 2024",
        ...     model="claude-4.5-sonnet",
        ...     max_iterations=10
        ... )
        >>> await agent.run()
        >>> print(agent.state.outline.title)
        'Generative AI market trends in 2024'
        >>> print(agent.state.evaluation_passed)
        True
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        topic: str,
        clarified_requirements: str = "",
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 10,
    ) -> Self:
        """새 OutlinerAgent 인스턴스를 생성하고 초기화합니다.

        Args:
            topic: 리포트 주제
            clarified_requirements: 명확화된 사용자 요구사항 (선택사항)
            model: 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
            max_iterations: 최대 반복 횟수 (기본값: 10)

        Returns:
            Self: 초기화된 OutlinerAgent 인스턴스
        """
        self = await super().setup()

        # 사용자 메시지 구성
        user_message_parts = [f"Topic: {topic}"]
        if clarified_requirements:
            user_message_parts.append(f"Requirements: {clarified_requirements}")

        # 상태 초기화
        self.state = OutlinerState(
            model=model,
            topic=topic,
            clarified_requirements=clarified_requirements,
            messages=[
                {"role": "system", "content": OUTLINER_SYSTEM_PROMPT},
                {"role": "user", "content": "\n".join(user_message_parts)},
            ],
        )

        # 도구 등록 (GenerateOutlineTool에 model 전달)
        self.tools = [
            SearchTool(),
            FetchTool(),
            GenerateOutlineTool(model=model),
        ]

        # 에이전트 설정
        self.max_iterations = max_iterations
        self.model = model
        self.stream = False

        self._initialized = True
        return self

    def _should_stop(self) -> bool:
        """에이전트가 실행을 중단해야 하는지 확인합니다.

        기본 종료 조건(최대 반복 횟수)에 더해, 평가를 통과했는지 확인합니다.

        Returns:
            bool: 에이전트가 중단해야 하면 True, 계속하려면 False
        """
        if super()._should_stop():
            return True
        return self.state.evaluation_passed
