"""비용 최적화된 검색 도구, 검색 결과 필터링, 그리고 최적화된 SearchAgent.

SearchAgent 파라미터 제한
- OptimizedSearchTool: 쿼리 수(최대 3개)와 결과 수(20개)를 제한하여 비용 절감

검색 결과 선별 전달
- filter_references_by_relevance: LLM 기반으로 관련 있는 검색 결과만 선별

최적화된 SearchAgent
- OptimizedSearchAgent: 파라미터 제한 + 결과 필터링을 에이전트 내부에서 처리
"""

import logging
from typing import Any

from langfuse.decorators import langfuse_context, observe
from pydantic import BaseModel
from typing_extensions import Self

from lec02_02_langfuse.router import router
from lec04_01_base_agent.state import TState
from lec04_01_base_agent.tool import ToolResult
from lec04_02_tools.fetch import FetchTool
from lec04_02_tools.schemas import ReferenceDocument
from lec04_02_tools.search import SearchTool
from lec05_02_researcher.schemas import RequiredInfo
from lec05_02_researcher.search_agent import SearchAgent
from lec05_02_researcher.search_agent_tools import submit_research_tool
from lec08_04_cost.model_selector import ModelSelector, TaskType

logger = logging.getLogger(__name__)


# =============================================================================
# OptimizedSearchTool — 파라미터 제한
# =============================================================================


class OptimizedSearchTool(SearchTool[TState]):
    """비용 최적화된 SearchTool.

    - 동시 생성 queries를 최대 5개로 제한 (스키마 + 런타임 모두 적용)
    - num_results를 20으로 고정
    """

    MAX_QUERIES = 5
    FIXED_NUM_RESULTS = 20

    description = (
        "Search the web for information. Returns search result snippets with titles and URLs. "
        "Pass up to 5 queries in the `queries` array to search different aspects of a topic in parallel. "
        "Craft queries to cover diverse angles (e.g., background, trends, challenges) for broader coverage."
    )
    parameters = {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": MAX_QUERIES,
                "description": f"List of search queries to execute (maximum {MAX_QUERIES})",
            },
            "num_results": {
                "type": "integer",
                "default": FIXED_NUM_RESULTS,
                "description": f"Number of results per query (fixed at {FIXED_NUM_RESULTS})",
            },
        },
        "required": ["queries"],
        "additionalProperties": False,
    }

    async def _execute(self, state: TState, **kwargs: Any) -> ToolResult:
        """쿼리 수와 결과 수를 제한한 뒤 검색을 실행합니다."""
        queries = kwargs.get("queries", [])[: self.MAX_QUERIES]
        kwargs["queries"] = queries
        kwargs["num_results"] = self.FIXED_NUM_RESULTS

        logger.info(
            "OptimizedSearchTool: queries=%d (max %d), num_results=%d",
            len(queries),
            self.MAX_QUERIES,
            self.FIXED_NUM_RESULTS,
        )

        return await super()._execute(state, **kwargs)


class FilteringSearchTool(OptimizedSearchTool):
    """검색 후 LLM 기반 관련성 필터링을 자동 수행하는 SearchTool.

    OptimizedSearchTool의 파라미터 제한에 더해, 매 검색 호출마다
    filter_references_by_relevance로 관련 결과만 선별합니다.
    필터된 결과만 state.reference_documents와 tool result(history)에 남습니다.

    SearchAgentState처럼 section_title, section_description, required_info가
    있는 state에서만 필터링이 동작합니다.
    """

    @observe(name="filtering_search_tool", capture_input=True, capture_output=True)
    async def _execute(self, state: TState, **kwargs: Any) -> ToolResult:
        """검색 실행 후 결과를 필터링합니다."""
        # 기존 문서 수 기록 (새로 추가된 문서만 필터링하기 위함)
        existing_count = len(getattr(state, "reference_documents", []))

        # 검색 실행 (OptimizedSearchTool → SearchTool)
        result = await super()._execute(state, **kwargs)

        # section context가 없으면 필터링 불가 (OutlinerAgent 등)
        if not hasattr(state, "section_title") or not hasattr(state, "required_info"):
            return result

        all_docs: list[ReferenceDocument] = getattr(state, "reference_documents", [])
        existing_docs = all_docs[:existing_count]
        new_docs = all_docs[existing_count:]

        if not new_docs:
            return result

        # LLM 기반 관련성 필터링
        filtered_docs = await filter_references_by_relevance(
            reference_documents=new_docs,
            section_title=state.section_title,  # type: ignore[attr-defined]
            section_description=state.section_description,  # type: ignore[attr-defined]
            required_info=state.required_info,  # type: ignore[attr-defined]
        )

        # state에 필터된 문서만 유지
        state.reference_documents = existing_docs + filtered_docs  # type: ignore[attr-defined]

        # 필터된 결과로 tool result 재구성 (history에 필터된 결과만 남김)
        content = self._format_filtered_content(filtered_docs, total_before=len(new_docs))

        logger.info(
            "FilteringSearchTool: %d -> %d docs (section: %s)",
            len(new_docs),
            len(filtered_docs),
            getattr(state, "section_title", "unknown"),
        )

        return ToolResult(content=content, artifact=result.artifact)

    @staticmethod
    def _format_filtered_content(filtered_docs: list[ReferenceDocument], total_before: int) -> str:
        """필터된 검색 결과를 포맷팅합니다."""
        if not filtered_docs:
            return f"Searched {total_before} results, but none were relevant to the section."

        lines = [
            f"Found {total_before} results, filtered to {len(filtered_docs)} relevant results:\n"
        ]
        for i, doc in enumerate(filtered_docs, 1):
            lines.append(f"{i}. {doc.title}")
            lines.append(f"   URL: {doc.url}")
            lines.append(f"   Snippet: {doc.snippet}")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# 검색 결과 선별 전달
# =============================================================================

FILTER_PROMPT_TEMPLATE = """\
You are a expert for relevance judgement. Given a list of search results and the research context, \
select only the results that are relevant and useful for writing the section.

## Section Context
- Title: {section_title}
- Description: {section_description}

## Required Information
{required_info_text}

## Search Results
{results_text}

Select the indices (0-based) of the most relevant results.
Only select results that directly contribute to answering the required information items.
"""


class _FilterResponse(BaseModel):
    """LLM 필터링 응답 스키마."""

    selected_indices: list[int]


@observe(capture_input=True, capture_output=True)
async def filter_references_by_relevance(
    reference_documents: list[ReferenceDocument],
    section_title: str,
    section_description: str,
    required_info: list[RequiredInfo],
) -> list[ReferenceDocument]:
    """LLM 기반으로 관련 있는 검색 결과만 선별합니다.

    각 ReferenceDocument의 title + snippet을 LLM에 제시하고,
    섹션 제목/설명 + required_info를 기준으로 관련성을 판단합니다.

    Args:
        reference_documents: 필터링할 참조 문서 리스트
        section_title: 섹션 제목
        section_description: 섹션 설명
        required_info: 필요 정보 항목 리스트

    Returns:
        선별된 참조 문서 리스트
    """
    # 필요 정보 텍스트 구성
    required_info_text = "\n".join(
        f"  {i}. {info.description}" for i, info in enumerate(required_info, 1)
    )

    # 검색 결과 텍스트 구성
    results_lines: list[str] = []
    for i, doc in enumerate(reference_documents):
        results_lines.append(f"[{i}] {doc.title}")
        results_lines.append(f"    URL: {doc.url}")
        results_lines.append(f"    Snippet: {doc.snippet}")
    results_text = "\n".join(results_lines)

    prompt = FILTER_PROMPT_TEMPLATE.format(
        section_title=section_title,
        section_description=section_description,
        required_info_text=required_info_text,
        results_text=results_text,
    )

    selector = ModelSelector()
    model = selector.select(TaskType.RESULT_FILTERING).model

    try:
        response: _FilterResponse = await router.acompletion_with_response_model(
            response_model=_FilterResponse,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        )

        # 유효한 인덱스만 필터링
        valid_indices = [
            idx for idx in response.selected_indices if 0 <= idx < len(reference_documents)
        ]

        filtered = [reference_documents[idx] for idx in valid_indices]

        logger.info(
            "filter_references_by_relevance: %d -> %d docs (section: %s)",
            len(reference_documents),
            len(filtered),
            section_title,
        )

        return filtered

    except Exception:
        logger.warning(
            "filter_references_by_relevance failed for section '%s', returning original docs",
            section_title,
            exc_info=True,
        )
        return reference_documents


# =============================================================================
# OptimizedSearchAgent — 파라미터 제한 + 결과 필터링
# =============================================================================


class OptimizedSearchAgent(SearchAgent):
    """비용 최적화된 SearchAgent.

    SearchAgent를 상속하여 검색 최적화를 에이전트 내부에서 처리합니다:
    - max_iterations: 10 → 7로 제한
    - SearchTool → FilteringSearchTool (쿼리 최대 5개, 결과 20개 + LLM 기반 필터링)
    - 매 search_web 호출마다 관련성 필터링 수행 → 필터된 결과만 history에 유지

    기존 방식은 ResearcherWorkflow에서 도구 교체와 필터링을 외부에서 처리했으나,
    이 클래스는 SearchAgent 자체가 최적화를 캡슐화합니다.
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        section_title: str,
        section_description: str,
        required_info: list[RequiredInfo],
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 7,
    ) -> Self:
        """최적화된 SearchAgent를 생성합니다.

        Args:
            section_title: 리서치 대상 섹션의 제목
            section_description: 리서치 대상 섹션의 설명
            required_info: 섹션 작성에 필요한 정보 항목 리스트
            model: 사용할 LLM 모델 이름 (기본값: "claude-4.5-sonnet")
            max_iterations: 최대 반복 횟수 (기본값: 7)

        Returns:
            초기화된 OptimizedSearchAgent 인스턴스
        """
        self = await super().setup(
            section_title=section_title,
            section_description=section_description,
            required_info=required_info,
            model=model,
            max_iterations=max_iterations,
        )

        # FilteringSearchTool로 교체 (검색 + 자동 필터링)
        self.tools = [
            FilteringSearchTool(),
            FetchTool(),
            submit_research_tool,
        ]

        logger.info(
            "OptimizedSearchAgent for '%s': max_iterations=%d, FilteringSearchTool applied",
            section_title,
            max_iterations,
        )

        return self
