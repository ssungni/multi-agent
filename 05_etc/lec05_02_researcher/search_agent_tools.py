"""Search Agent 도구 모듈.

SearchAgent에서 사용하는 리서치 제출 도구를 제공합니다.
"""

from typing import Any

from lec04_01_base_agent.tool import BaseTool, ToolResult
from lec05_02_researcher.schemas import SectionResearch
from lec05_02_researcher.search_agent_state import SearchAgentState


class SubmitResearchTool(BaseTool[SearchAgentState]):
    """수집된 정보를 바탕으로 섹션 리서치를 제출합니다.

    검색 결과와 페치한 콘텐츠를 기반으로 섹션 리서치를 생성하고 상태에 저장합니다.
    """

    name = "submit_research"
    description = (
        "Submit research results for the section with a summary of collected information. "
        "Call this after gathering sufficient search results and fetched content."
    )
    parameters = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Summary of the key information collected for this section",
            },
        },
        "required": ["summary"],
        "additionalProperties": False,
    }

    async def _execute(self, state: SearchAgentState, **kwargs: Any) -> ToolResult:
        """섹션 리서치를 제출하고 상태에 저장합니다.

        LLM이 summary만 전달하고, reference_documents는
        state.reference_documents에서 자동으로 수집합니다.

        Args:
            state: 현재 SearchAgentState
            **kwargs: summary (str) - 수집된 정보의 요약

        Returns:
            제출 확인 메시지를 담은 ToolResult
        """
        summary: str = kwargs.get("summary", "")

        if not summary:
            raise ValueError("summary is required")

        # SectionResearch 생성
        section_research = SectionResearch(
            section_title=state.section_title,
            section_description=state.section_description,
            required_info=state.required_info,
            reference_documents=list(state.reference_documents),
            summary=summary,
        )

        # 상태 업데이트
        state.section_research = section_research

        # 결과 메시지 구성
        fetched_count = sum(1 for doc in state.reference_documents if doc.content is not None)
        content = (
            f"Research submitted for section '{state.section_title}'.\n"
            f"Reference documents: {len(state.reference_documents)}\n"
            f"Fetched pages: {fetched_count}"
        )

        state.submitted_research = True

        return ToolResult(content=content, artifact=section_research)


# Module-level instance
submit_research_tool = SubmitResearchTool()
