"""Writer Agent 구현.

리서치 결과를 기반으로 리포트를 작성하는 WriterAgent를 정의합니다.
WriterAgent는 오케스트레이터로서 각 섹션의 작성을 WriteSectionTool에 위임하고,
도구 내부의 SectionEvaluator/ReportEvaluator를 통한 품질 검증 루프를 활용합니다.
"""

from langfuse.decorators import observe
from typing_extensions import Self

from lec04_01_base_agent.base import BaseAgent
from lec05_01_outliner.schemas import Outline
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer.prompts import WRITER_SYSTEM_PROMPT
from lec05_03_writer.state import WriterState
from lec05_03_writer.tools import PolishReportTool, WriteSectionTool


class WriterAgent(BaseAgent[WriterState]):
    """리서치 결과를 기반으로 리포트를 작성하는 오케스트레이터 에이전트.

    이 에이전트는 직접 섹션 콘텐츠를 작성하지 않고, WriteSectionTool에
    섹션 작성을 위임합니다. WriteSectionTool은 별도의 LLM 호출로 해당 섹션의
    리서치 데이터를 활용하여 콘텐츠를 독립적으로 생성합니다.

    에이전트는 다음 단계를 수행합니다:

    1. **섹션 작성 위임**: 각 섹션에 대해 WriteSectionTool 호출 (별도 LLM이 작성+평가)
    2. **리포트 통합**: PolishReportTool로 모든 섹션을 하나의 리포트로 통합+평가

    각 도구는 내부에서 Evaluator 기반 평가 루프를 수행합니다:

    - **WriteSectionTool**: SectionEvaluator로 섹션 품질을 검증하고,
      미달 시 피드백을 반영하여 재작성합니다.

    - **PolishReportTool**: ReportEvaluator로 전체 리포트 품질을 검증하고,
      미달 시 피드백을 반영하여 재통합합니다.

    Attributes:
        state: 에이전트의 실행 상태 (WriterState)
        tools: 사용 가능한 도구 목록 (WriteSectionTool, PolishReportTool)
        max_iterations: 최대 반복 횟수
        model: 사용할 LLM 모델 이름
        stream: 스트리밍 모드 사용 여부

    Example:
        >>> agent = await WriterAgent.setup(
        ...     outline=outline,
        ...     section_research=section_research_results,
        ...     model="claude-4.5-sonnet",
        ...     max_iterations=20
        ... )
        >>> await agent.run()
        >>> print(agent.state.final_report.title)
        >>> print(agent.state.report_evaluation_passed)
        True
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        outline: Outline,
        section_research: dict[str, SectionResearch],
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 20,
    ) -> Self:
        """새 WriterAgent 인스턴스를 생성하고 초기화합니다.

        Args:
            outline: Outliner Agent가 생성한 아웃라인
            section_research: 섹션 제목을 키로 하는 리서치 결과 딕셔너리
            model: 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
            max_iterations: 최대 반복 횟수 (기본값: 20)

        Returns:
            Self: 초기화된 WriterAgent 인스턴스

        Raises:
            RuntimeError: setup()이 이미 초기화된 에이전트에서 호출된 경우
        """
        self = await super().setup()

        # 아웃라인 정보를 사용자 메시지로 구성 (리서치 데이터는 WriteSectionTool이 직접 접근)
        user_message = self._build_initial_message(outline)

        # 상태 초기화
        self.state = WriterState(
            model=model,
            outline=outline,
            section_research=section_research,
            messages=[
                {"role": "system", "content": WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )

        # 도구 등록 (도구에 model 전달)
        self.tools = [
            WriteSectionTool(model=model),
            PolishReportTool(model=model),
        ]

        # 에이전트 설정
        self.max_iterations = max_iterations
        self.model = model
        self.stream = False

        self._initialized = True
        return self

    @staticmethod
    def _build_initial_message(outline: Outline) -> str:
        """초기 사용자 메시지를 구성합니다.

        아웃라인 구조만 포함합니다. 리서치 데이터는 WriteSectionTool이
        상태에서 직접 접근하여 별도의 LLM 호출에 사용합니다.

        Args:
            outline: 리포트 아웃라인

        Returns:
            구성된 사용자 메시지 문자열
        """
        parts: list[str] = [
            "Write a report based on the following outline.\n",
            f"Report title: {outline.title}\n",
            "## Sections to Write\n",
        ]

        for i, section in enumerate(outline.sections, 1):
            parts.append(f"{i}. **{section.title}**")
            parts.append(f"   Description: {section.description}")
            if section.subsections:
                parts.append(f"   Subsections: {', '.join(section.subsections)}")
            parts.append("")

        return "\n".join(parts)

    def _should_stop(self) -> bool:
        """에이전트가 실행을 중단해야 하는지 확인합니다.

        기본 종료 조건(최대 반복 횟수)에 더해, 리포트 평가가 통과했는지 확인합니다.

        Returns:
            bool: 에이전트가 중단해야 하면 True, 계속하려면 False

        Raises:
            MaxIterationError: max_iterations를 초과한 경우
        """
        if super()._should_stop():
            return True
        return self.state.report_evaluation_passed
