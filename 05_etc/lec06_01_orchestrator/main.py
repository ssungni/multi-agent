"""Lecture 06-01 통합 실행 예제 - Orchestrator Agent 데모.

이 모듈은 OrchestratorAgent의 동작을 시연하는 종합 예제입니다.
Sub-agent들을 조율하여 주제에 대한 전체 리포트를 자동 생성합니다.

학습 포인트:
    1. Sub-agent 호출 패턴 (Constructor Injection)
       - OutlinerAgent, ResearcherAgent, WriterAgent를 Tool로 감싸서 호출
       - 순환 import 방지를 위한 Constructor Injection 패턴
    2. 워크플로우 상태 관리 (Phase)
       - OUTLINE_GENERATION → RESEARCH → WRITING → COMPLETE
       - 각 단계별 데이터 흐름 추적
    3. 중앙 집중식 워크플로우 제어
       - Orchestrator가 전체 파이프라인을 제어
       - Sub-agent 간 데이터 전달 관리

실행 방법:
    rye run lec06-01

전체 워크플로우:
    User Input ("2025년 생성형 AI 시장 동향")
        └── OrchestratorAgent.setup()
              └── OrchestratorState 초기화 (Phase: OUTLINE_GENERATION)
              └── Tools 등록 (CallOutlinerTool, CallResearcherTool,
                              CallWriterTool, FinalAnswerTool)
        └── OrchestratorAgent.run()
              └── Phase 1: call_outliner
                    └── OutlinerAgent 생성 및 실행
                    └── 아웃라인 결과를 부모 상태에 병합
              └── Phase 2: call_researcher
                    └── ResearcherAgent 생성 및 실행
                    └── 리서치 결과를 부모 상태에 병합
              └── Phase 3: call_writer
                    └── WriterAgent 생성 및 실행
                    └── 최종 리포트를 부모 상태에 병합
              └── Phase 4: final_answer
                    └── 최종 리포트를 사용자에게 전달
                    └── Phase → COMPLETE
        └── Final Report 출력

참고:
    - OrchestratorAgent: lecture/lec06_01_orchestrator/agent.py
    - Architecture: archiecture/orchestrator.md
    - OutlinerAgent: lecture/lec05_01_outliner/agent.py
    - ResearcherAgent: lecture/lec05_02_researcher/agent.py
    - WriterAgent: lecture/lec05_03_writer/agent.py
"""

import asyncio
import os
import sys

from lec06_01_orchestrator.agent import OrchestratorAgent


def print_report(agent: OrchestratorAgent) -> None:
    """최종 리포트를 보기 좋게 출력합니다.

    Args:
        agent: OrchestratorAgent 인스턴스
    """
    if not agent.state.final_report:
        print("리포트가 생성되지 않았습니다.")
        return

    report = agent.state.final_report

    print("\n" + "=" * 80)
    print("최종 리포트")
    print("=" * 80 + "\n")
    print(f"# {report.title}\n")

    for section in report.sections:
        print(f"## {section.title}\n")
        print(section.content)
        if section.sources:
            print("\n출처:")
            for source in section.sources:
                print(f"  - {source}")
        print()

    if report.references:
        print("-" * 80)
        print("\n## 참고 문헌\n")
        for i, ref in enumerate(report.references, 1):
            print(f"  {i}. {ref}")

    print("\n" + "=" * 80)


async def main() -> None:
    """메인 데모 함수."""
    print("\n" + "=" * 80)
    print("Lecture 06-01: Orchestrator Agent 데모")
    print("=" * 80)

    # SERPER_API_KEY 확인
    if not os.environ.get("SERPER_API_KEY"):
        print("\n오류: SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Serper API 키는 https://serper.dev 에서 발급받을 수 있습니다.")
        print("\n사용법:")
        print("  export SERPER_API_KEY='your-api-key'")
        print("  rye run lec06-01")
        sys.exit(1)

    # 데모 주제
    user_request = "2025년 생성형 AI 시장 동향에 대한 리포트를 작성해주세요."

    print(f"\n요청: {user_request}")
    print("\nOrchestratorAgent를 초기화합니다...")

    try:
        # OrchestratorAgent 설정
        agent = await OrchestratorAgent.setup(
            user_request=user_request,
            model="claude-4.5-sonnet",
            max_iterations=20,
        )

        print("OrchestratorAgent 실행 중...\n")
        print("=" * 80)
        print("워크플로우 실행 과정")
        print("=" * 80)
        print("(Outliner → Researcher → Writer → Final Report)")
        print()

        # 에이전트 실행
        await agent.run()

        # 결과 출력
        print("\n" + "=" * 80)
        print("워크플로우 실행 완료")
        print("=" * 80)
        print(f"현재 Phase: {agent.state.current_phase.value}")
        print(f"총 반복 횟수: {agent.state.iteration_count}")

        if agent.state.outline:
            print(f"아웃라인 섹션 수: {len(agent.state.outline.sections)}")
        print(f"리서치 완료 섹션 수: {len(agent.state.research_results)}")
        print(f"참조 문서 수: {len(agent.state.reference_documents)}")

        # 리포트 출력
        print_report(agent)

        print("\n" + "=" * 80)
        print("데모 완료!")
        print("=" * 80 + "\n")

    except Exception as e:
        print("\n" + "=" * 80)
        print("오류 발생")
        print("=" * 80)
        print(f"오류 메시지: {e}")
        print("\n일반적인 문제:")
        print("1. SERPER_API_KEY가 올바르게 설정되지 않음")
        print("2. 네트워크 연결 문제")
        print("3. API 할당량 초과")
        print("=" * 80 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
