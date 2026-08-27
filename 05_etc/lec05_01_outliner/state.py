"""Outliner Agent 상태 관리 모듈.

Outliner Agent의 실행 상태를 추적하는 OutlinerState 모델을 정의합니다.
주제 명확화, 검색 결과 수집, 아웃라인 생성 및 평가 과정의 상태를 관리합니다.
"""

from lec04_01_base_agent.state import BaseAgentState
from lec04_02_tools.schemas import ReferenceDocument
from lec05_01_outliner.schemas import Outline


class OutlinerState(BaseAgentState):
    """Outliner Agent의 상태를 관리하는 모델.

    사용자 주제로부터 구조화된 아웃라인을 생성하는 과정의 상태를 추적합니다.
    주제 명확화, 검색 결과 수집, 아웃라인 생성, 평가 피드백 등의 정보를 포함합니다.

    Attributes:
        topic: 리포트 주제
        clarified_requirements: 명확화된 사용자 요구사항
        search_results: 수집된 검색 결과 리스트
        outline: 생성된 아웃라인 (없으면 None)
        evaluation_feedback: Evaluator의 피드백 메시지
        evaluation_passed: 평가 통과 여부
    """

    topic: str
    clarified_requirements: str = ""
    reference_documents: list[ReferenceDocument] = []
    outline: Outline | None = None
    evaluation_feedback: str | None = None
    evaluation_passed: bool = False
