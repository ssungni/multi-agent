"""웹 검색 도구 모듈.

Serper API를 사용하여 웹 검색을 수행하고 결과 스니펫을 반환하는 SearchTool을 제공합니다.
"""

import asyncio
import os
from typing import Any

import httpx

from lec04_01_base_agent.state import TState
from lec04_01_base_agent.tool import BaseTool, ToolResult
from lec04_02_tools.schemas import ReferenceDocument, SearchResult


class SearchTool(BaseTool[TState]):
    """웹 검색을 수행하고 결과 스니펫을 반환합니다.

    Serper API를 사용하여 여러 검색 쿼리를 병렬로 실행하고,
    각 결과의 제목, URL, 스니펫을 반환합니다.

    상태에 reference_documents 속성이 있으면 검색 결과를 저장합니다.
    """

    name = "search_web"
    description = (
        "Search the web for information. Returns search result snippets with titles and URLs. "
        "Pass multiple queries in the `queries` array to search different aspects of a topic in parallel. "
        "Craft queries to cover diverse angles (e.g., background, trends, challenges, applications) for broader coverage."
    )
    parameters = {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of search queries to execute",
            },
            "num_results": {
                "type": "integer",
                "default": 3,
                "description": "Number of results per query",
            },
        },
        "required": ["queries"],
        "additionalProperties": False,
    }

    async def _execute(self, state: TState, **kwargs: Any) -> ToolResult:
        """웹 검색을 실행합니다.

        Args:
            state: 현재 에이전트 상태
            **kwargs: queries (list[str]) 및 num_results (int, 기본값 5)

        Returns:
            검색 결과를 담은 ToolResult

        Raises:
            ValueError: API 키가 설정되지 않았거나 쿼리가 비어있을 때
            Exception: 검색 실패 시
        """
        queries: list[str] = kwargs.get("queries", [])
        num_results: int = kwargs.get("num_results", 20)

        if not queries:
            raise ValueError("At least one query is required")

        api_key = os.environ.get("SERPER_API_KEY")
        if not api_key:
            raise ValueError("SERPER_API_KEY environment variable is not set")

        try:
            # 모든 쿼리를 병렬로 실행
            all_results = await asyncio.gather(
                *[self._search_single_query(query, num_results, api_key) for query in queries]
            )

            # 결과를 평탄화
            search_results: list[SearchResult] = []
            for results in all_results:
                search_results.extend(results)

            # 상태에 reference_documents 속성이 있으면 저장 (duck typing)
            if hasattr(state, "reference_documents"):
                reference_docs = [
                    ReferenceDocument(
                        title=result.title,
                        url=result.url,
                        snippet=result.snippet,
                        content=None,
                    )
                    for result in search_results
                ]
                # 기존 문서에 추가
                existing_docs = getattr(state, "reference_documents", [])
                state.reference_documents = existing_docs + reference_docs  # type: ignore

            # 결과를 포맷팅
            content = self._format_results(queries, search_results)

            return ToolResult(content=content, artifact=search_results)

        except httpx.HTTPError as e:
            raise Exception(f"HTTP error during search: {e}") from e
        except Exception as e:
            raise Exception(f"Search failed: {e}") from e

    async def _search_single_query(
        self, query: str, num_results: int, api_key: str
    ) -> list[SearchResult]:
        """단일 쿼리에 대한 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            num_results: 반환할 결과 수
            api_key: Serper API 키

        Returns:
            검색 결과 리스트

        Raises:
            httpx.HTTPError: HTTP 요청 실패 시
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": num_results},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # organic 검색 결과를 SearchResult 객체로 변환
            results = []
            for item in data.get("organic", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                    )
                )

            return results

    def _format_results(self, queries: list[str], results: list[SearchResult]) -> str:
        """검색 결과를 포맷팅합니다.

        Args:
            queries: 실행된 쿼리 리스트
            results: 검색 결과 리스트

        Returns:
            포맷팅된 검색 결과 문자열
        """
        if not results:
            return f"No results found for queries: {', '.join(queries)}"

        lines = [f"Found {len(results)} search results for queries: {', '.join(queries)}\n"]

        for i, result in enumerate(results, 1):
            lines.append(f"{i}. {result.title}")
            lines.append(f"   URL: {result.url}")
            lines.append(f"   Snippet: {result.snippet}")
            lines.append("")  # 빈 줄 추가

        return "\n".join(lines)
