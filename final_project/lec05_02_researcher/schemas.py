"""Researcher Agent를 위한 스키마 모듈.

ResearcherWorkflow에서 사용하는 리서치 데이터 모델을 정의합니다.
섹션별 필요 정보 정의와 리서치 결과를 구조화하여 표현합니다.
"""

from pydantic import BaseModel, Field

from lec04_02_tools.schemas import ReferenceDocument


class RequiredInfo(BaseModel):
    """섹션 작성에 필요한 정보 항목.

    아웃라인의 각 섹션을 작성하기 위해 수집해야 할 구체적인 정보를 정의합니다.
    각 항목은 검색 가능한 형태로 정의되어야 합니다.

    Attributes:
        description: 필요한 정보에 대한 구체적인 설명
        covered: 해당 정보가 충분히 수집되었는지 여부 (기본값: False)
    """

    description: str
    covered: bool = False


class SectionRequiredInfo(BaseModel):
    """개별 섹션에 대한 필요 정보 정의.

    LLM 구조화된 출력으로 사용됩니다.

    Attributes:
        section_title: 섹션 제목
        required_info: 해당 섹션에 필요한 정보 항목 리스트
    """

    section_title: str = Field(description="Title of the outline section")
    required_info: list[RequiredInfo] = Field(
        description="List of specific information items needed for this section (3-6 items)"
    )


class RequiredInfoDefinition(BaseModel):
    """전체 아웃라인에 대한 필요 정보 정의 결과.

    LLM 구조화된 출력으로 사용됩니다.

    Attributes:
        sections: 섹션별 필요 정보 정의 리스트
    """

    sections: list[SectionRequiredInfo] = Field(
        description="Required information definitions for each section of the outline"
    )


class SectionResearch(BaseModel):
    """섹션별 리서치 결과.

    아웃라인의 개별 섹션에 대해 수행된 리서치의 전체 결과를 포함합니다.
    필요 정보 정의, 참조 문서, 요약을 포함합니다.

    Attributes:
        section_title: 리서치 대상 섹션의 제목
        section_description: 리서치 대상 섹션의 설명
        required_info: 섹션 작성에 필요한 정보 항목 리스트
        reference_documents: 수집된 참조 문서 리스트 (검색 결과 + 페치한 콘텐츠 통합)
        summary: 수집된 정보의 요약
        research_complete: 리서치 완료 여부
    """

    section_title: str
    section_description: str = ""
    required_info: list[RequiredInfo] = []
    reference_documents: list[ReferenceDocument] = []
    summary: str = ""
    research_complete: bool = False
