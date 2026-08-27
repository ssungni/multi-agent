"""웹 페이지 콘텐츠 추출 도구 모듈.

httpx와 BeautifulSoup을 사용하여 웹페이지에서 메인 콘텐츠를 추출하는 FetchTool을 제공합니다.
"""

from typing import Any

import httpx
from bs4 import BeautifulSoup, Tag

from lec04_01_base_agent.state import TState
from lec04_01_base_agent.tool import BaseTool, ToolResult

# 최대 콘텐츠 길이 제한 (컨텍스트 윈도우 관리)
MAX_CONTENT_LENGTH = 10_000
# HTTP 요청 타임아웃 (초)
REQUEST_TIMEOUT = 30.0


class FetchTool(BaseTool[TState]):
    """웹페이지에서 메인 콘텐츠를 추출합니다.

    httpx를 사용하여 비동기적으로 웹페이지를 가져오고,
    BeautifulSoup으로 파싱하여 메인 콘텐츠만 추출합니다.

    상태에 document_full_text_map 속성이 있으면 추출한 콘텐츠를 캐싱합니다.
    """

    name = "fetch_webpage"
    description = (
        "Fetch and extract main content from a webpage URL. "
        "Use selectively when search snippets lack sufficient detail. "
        "Limit to 2-3 pages at a time to avoid information overload."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
        },
        "required": ["url"],
        "additionalProperties": False,
    }

    async def _execute(self, state: TState, **kwargs: Any) -> ToolResult:
        """웹페이지를 가져와서 메인 콘텐츠를 추출합니다.

        Args:
            state: 현재 에이전트 상태
            **kwargs: url (str)

        Returns:
            추출된 콘텐츠를 담은 ToolResult

        Raises:
            ValueError: URL이 제공되지 않았을 때
            Exception: HTTP 요청 실패 또는 파싱 실패 시
        """
        url: str = kwargs.get("url", "")

        if not url:
            raise ValueError("URL is required")

        try:
            # HTTP 요청 (User-Agent 헤더 포함)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    timeout=REQUEST_TIMEOUT,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    },
                )
                response.raise_for_status()

            # HTML 파싱
            soup = BeautifulSoup(response.text, "html.parser")

            # 메인 콘텐츠 추출
            content = self._extract_main_content(soup)

            if not content:
                content = "[No readable content found on this page]"

            # 상태의 reference_documents에서 해당 URL의 ReferenceDocument 업데이트
            if hasattr(state, "reference_documents"):
                for doc in state.reference_documents:  # type: ignore
                    if doc.url == url:
                        doc.content = content
                        break

            # 상태의 document_full_text_map에 캐싱 (if exists)
            if hasattr(state, "document_full_text_map"):
                state.document_full_text_map[url] = content  # type: ignore

            return ToolResult(content=content, artifact={"url": url, "length": len(content)})

        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error fetching {url}: {e.response.status_code}") from e
        except httpx.TimeoutException as e:
            raise Exception(f"Timeout fetching {url}: {e}") from e
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error fetching {url}: {e}") from e
        except Exception as e:
            raise Exception(f"Failed to fetch and parse {url}: {e}") from e

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """HTML에서 메인 콘텐츠를 추출합니다.

        Args:
            soup: BeautifulSoup 객체

        Returns:
            추출된 텍스트 콘텐츠
        """
        # 불필요한 태그 제거
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # 메인 콘텐츠 영역 찾기
        main_content: Tag | None = None
        for selector in ["article", "main", "div[role='main']"]:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # 메인 콘텐츠 영역이 없으면 body 사용
        if not main_content:
            main_content = soup.body

        if not main_content:
            # body도 없으면 전체 soup 사용
            main_content = soup

        # 단락과 제목에서 텍스트 추출
        text_parts: list[str] = []
        for tag in main_content.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
            text = tag.get_text(strip=True)
            if text:
                text_parts.append(text)

        # 텍스트 결합 및 정리
        content = "\n\n".join(text_parts)

        # 연속된 공백 제거
        import re

        content = re.sub(r"\s+", " ", content)
        content = re.sub(r"\n\s*\n+", "\n\n", content)

        # 길이 제한
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH] + "\n\n[Content truncated due to length limit]"

        return content.strip()
