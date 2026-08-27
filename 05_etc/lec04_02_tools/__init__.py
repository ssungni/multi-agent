"""Lecture 04-02: Common Tools - 공통 도구 구현.

이 패키지는 Report Generation Agent의 공통 도구를 포함합니다:
- SearchTool: Serper API 기반 웹 검색 도구
- FetchTool: 웹페이지 콘텐츠 추출 도구
- SearchResult, ReferenceDocument: 검색 결과 스키마

이 도구들은 OutlinerAgent, ResearcherAgent에서 웹 정보를 수집하는 데 사용됩니다.
"""

from lec04_02_tools.fetch import FetchTool
from lec04_02_tools.schemas import ReferenceDocument, SearchResult
from lec04_02_tools.search import SearchTool

__all__ = [
    "FetchTool",
    "ReferenceDocument",
    "SearchResult",
    "SearchTool",
]
