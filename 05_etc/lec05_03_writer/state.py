"""Writer Agent 상태 관리 모듈.

Writer Agent의 실행 상태를 추적하는 WriterState 모델을 정의합니다.
아웃라인 수신, 섹션별 리서치 결과, 섹션 작성, 최종 리포트 생성 과정의 상태를 관리합니다.
"""

from lec04_01_base_agent.state import BaseAgentState
from lec05_01_outliner.schemas import Outline
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer.schemas import FinalReport, ReportSection


class WriterState(BaseAgentState):
    """Writer Agent의 상태를 관리하는 모델.

    리서치 결과를 기반으로 섹션별 콘텐츠를 작성하고, 전체 리포트를 통합하는
    과정의 상태를 추적합니다. 섹션 레벨과 리포트 레벨의 평가 상태를 포함합니다.

    Attributes:
        outline: Outliner Agent가 생성한 아웃라인
        section_research: 섹션 제목을 키로 하는 리서치 결과 딕셔너리
        written_sections: 작성 완료된 섹션 딕셔너리 (섹션 제목 → ReportSection)
        final_report: 최종 통합 리포트 (없으면 None)
        section_evaluation_feedback: SectionEvaluator의 피드백 (섹션 제목 → 피드백)
        sections_evaluation_passed: 모든 섹션의 평가 통과 여부
        report_evaluation_feedback: ReportEvaluator의 피드백 메시지
        report_evaluation_passed: 리포트 전체 평가 통과 여부
    """

    outline: Outline | None = None
    section_research: dict[str, SectionResearch] = {}
    written_sections: dict[str, ReportSection] = {}
    final_report: FinalReport | None = None
    section_evaluation_feedback: dict[str, str] = {}
    passed_sections: set[str] = set()
    sections_evaluation_passed: bool = False
    report_evaluation_feedback: str | None = None
    report_evaluation_passed: bool = False
