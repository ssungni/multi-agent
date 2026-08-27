"""Search Agent 구현.

개별 섹션에 대해 웹 검색과 콘텐츠 수집을 수행하는 SearchAgent를 정의합니다.
"""

from langfuse.decorators import observe
from typing_extensions import Self

from lec04_01_base_agent.base import BaseAgent
from lec04_01_base_agent.tool import BaseTool
from lec04_02_tools.fetch import FetchTool
from lec04_02_tools.search import SearchTool
from lec05_02_researcher.prompts import SEARCH_AGENT_SYSTEM_PROMPT
from lec05_02_researcher.schemas import RequiredInfo
from lec05_02_researcher.search_agent_state import SearchAgentState
from lec05_02_researcher.search_agent_tools import submit_research_tool

# Module-level tool instances
search_tool: SearchTool = SearchTool()
fetch_tool: FetchTool = FetchTool()

# Default tools for SearchAgent
SEARCH_AGENT_DEFAULT_TOOLS: list[BaseTool] = [
    search_tool,
    fetch_tool,
    submit_research_tool,
]


class SearchAgent(BaseAgent[SearchAgentState]):
    """개별 섹션에 대해 웹 검색과 콘텐츠 수집을 수행하는 에이전트.

    ResearcherWorkflow로부터 섹션 정보를 전달받아,
    해당 섹션에 필요한 정보를 검색하고 수집합니다.

    이 에이전트는 다음 단계를 수행합니다:

    1. **웹 검색**: 필요 정보 항목에 기반하여 다양한 검색 쿼리 생성 및 실행
    2. **콘텐츠 수집**: 검색 결과에서 유망한 페이지의 상세 콘텐츠 추출
    3. **리서치 제출**: 수집된 정보를 요약하여 SubmitResearchTool로 제출

    Attributes:
        state: 에이전트의 실행 상태 (SearchAgentState)
        tools: 사용 가능한 도구 목록 (SearchTool, FetchTool, SubmitResearchTool)
        max_iterations: 최대 반복 횟수
        model: 사용할 LLM 모델 이름
        stream: 스트리밍 모드 사용 여부

    Example:
        >>> agent = await SearchAgent.setup(
        ...     section_title="시장 규모",
        ...     section_description="글로벌 시장 규모 분석",
        ...     required_info=[RequiredInfo(description="2024년 시장 규모")],
        ...     model="claude-4.5-sonnet",
        ... )
        >>> await agent.run()
        >>> print(agent.state.section_research.summary)
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        section_title: str,
        section_description: str,
        required_info: list[RequiredInfo],
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 10,
    ) -> Self:
        """새 SearchAgent 인스턴스를 생성하고 초기화합니다.

        Args:
            section_title: 리서치 대상 섹션의 제목
            section_description: 리서치 대상 섹션의 설명
            required_info: 섹션 작성에 필요한 정보 항목 리스트
            model: 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
            max_iterations: 최대 반복 횟수 (기본값: 10)

        Returns:
            Self: 초기화된 SearchAgent 인스턴스
        """
        self = await super().setup()

        # 필요 정보를 사용자 메시지로 구성
        required_info_text = "\n".join(
            f"  {i}. {info.description}" for i, info in enumerate(required_info, 1)
        )
        user_message = (
            f"Research the following section:\n\n"
            f"Section title: {section_title}\n"
            f"Section description: {section_description}\n\n"
            f"Required information to collect:\n{required_info_text}\n\n"
            f"Search the web to gather comprehensive data for each required info item, "
            f"then submit your research using `submit_research`."
        )

        # 상태 초기화
        self.state = SearchAgentState(
            model=model,
            section_title=section_title,
            section_description=section_description,
            required_info=required_info,
            messages=[
                {"role": "system", "content": SEARCH_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )

        # 도구 등록
        self.tools = list(SEARCH_AGENT_DEFAULT_TOOLS)

        # 에이전트 설정
        self.max_iterations = max_iterations
        self.model = model
        self.stream = False

        self._initialized = True
        return self

    def _should_stop(self) -> bool:
        """에이전트가 실행을 중단해야 하는지 확인합니다.

        기본 종료 조건(최대 반복 횟수)에 더해, 리서치가 제출되었는지 확인합니다.

        Returns:
            bool: 에이전트가 중단해야 하면 True, 계속하려면 False

        Raises:
            MaxIterationError: max_iterations를 초과한 경우
        """
        if super()._should_stop():
            return True
        return self.state.section_research is not None and self.state.submitted_research
