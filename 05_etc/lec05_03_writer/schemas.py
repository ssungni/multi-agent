"""Writer Agent를 위한 스키마 모듈.

WriterAgent에서 사용하는 리포트 데이터 모델을 정의합니다.
개별 리포트 섹션과 최종 리포트를 구조화하여 표현합니다.
"""

from pydantic import BaseModel


class ReportSection(BaseModel):
    """리포트 섹션.

    리포트의 개별 섹션을 표현하는 모델입니다.
    각 섹션은 제목, 본문 콘텐츠, 그리고 참조 출처 목록을 포함합니다.

    Attributes:
        title: 섹션의 제목
        content: 섹션의 본문 콘텐츠 (마크다운 형식)
        sources: 섹션에서 인용한 출처 URL 리스트
    """

    title: str
    content: str
    sources: list[str] = []


class FinalReport(BaseModel):
    """최종 리포트.

    모든 섹션이 통합된 최종 리포트를 표현하는 모델입니다.
    제목, 섹션 목록, 그리고 전체 참고 문헌 리스트를 포함합니다.

    Attributes:
        title: 리포트의 제목
        sections: 리포트를 구성하는 섹션 목록
        references: 전체 참고 문헌 URL 리스트
    """

    title: str
    sections: list[ReportSection]
    references: list[str] = []
