"""도구 출력을 위한 공통 스키마 모듈.

SearchTool과 FetchTool에서 사용하는 데이터 모델을 정의합니다.
검색 결과와 참조 문서의 구조화된 데이터를 표현합니다.
"""

from pydantic import BaseModel


class SearchResult(BaseModel):
    """검색 결과.

    웹 검색 API(Serper 등)의 개별 검색 결과를 표현합니다.

    Attributes:
        title: 검색 결과의 제목
        url: 검색 결과 페이지의 URL
        snippet: 검색 결과의 요약 텍스트 (스니펫)
    """

    title: str
    url: str
    snippet: str


class ReferenceDocument(BaseModel):
    """참조 문서.

    검색 결과와 페치한 콘텐츠를 통합하여 표현하는 문서 모델입니다.
    SearchTool과 FetchTool 모두에서 사용됩니다.

    Attributes:
        title: 문서 제목
        url: 문서 URL
        snippet: 문서 요약 (검색 결과에서 제공)
        content: 페치한 전체 콘텐츠 (선택적, FetchTool 사용 시 채워짐)
    """

    title: str
    url: str
    snippet: str
    content: str | None = None
