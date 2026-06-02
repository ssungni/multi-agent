"""Outliner Agent를 위한 스키마 모듈.

OutlinerAgent에서 사용하는 아웃라인 데이터 모델을 정의합니다.
구조화된 아웃라인과 섹션 정보를 표현합니다.
"""

from pydantic import BaseModel


class OutlineSection(BaseModel):
    """아웃라인 섹션.

    아웃라인의 개별 섹션을 표현하는 모델입니다.
    각 섹션은 제목, 설명, 그리고 선택적으로 하위 섹션 목록을 포함합니다.

    Attributes:
        title: 섹션의 제목
        description: 섹션의 설명
        subsections: 하위 섹션 제목 목록 (선택적, 기본값: 빈 리스트)
    """

    title: str
    description: str
    subsections: list[str] = []


class Outline(BaseModel):
    """생성된 아웃라인.

    사용자 주제로부터 생성된 전체 아웃라인을 표현하는 모델입니다.
    여러 섹션으로 구성된 구조화된 아웃라인을 나타냅니다.

    Attributes:
        title: 아웃라인의 제목
        sections: 아웃라인을 구성하는 섹션 목록
    """

    title: str
    sections: list[OutlineSection]
