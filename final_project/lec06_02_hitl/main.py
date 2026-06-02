"""Lecture 06-02 통합 실행 예제 - HITL 메커니즘 데모.

이 모듈은 HITL (Human-In-The-Loop) 메커니즘의 동작을 시연하는 종합 예제입니다.
lec06_02_hitl의 HITLOrchestratorAgent를 사용하여, 아웃라인 승인(ask_outline_approval)
단계에서 사용자 인터랙션을 받는 전체 워크플로우를 보여줍니다.

학습 포인트:
    1. HITL 메커니즘의 전체 흐름 이해
       - Tool이 HITLData를 반환하여 인터럽트 발생
       - Agent가 HITL 인터럽트를 감지하고 일시 정지
       - 사용자 응답으로 Agent 재개
    2. mode="tool_result" HITL 모드
       - ask_outline_approval: 사용자가 직접 결과(승인/거부) 제공
       - 승인 시: 다음 단계(Research)로 진행
       - 거부 시: revision feedback와 함께 Outliner 재호출
    3. HITL 재개 메커니즘 (_resume_hitl)
       - mode="tool_result": 사용자 응답을 tool message로 주입
       - rejected=True: 사용자가 거부한 경우

실행 방법:
    rye run lec06-02

HITL Orchestrator 흐름:
    User Request ("2025년 생성형 AI 시장 동향에 대한 리포트 작성")
        └── HITLOrchestratorAgent.setup()
              └── Tools: CallOutliner, AskOutlineApproval,
                         CallResearcher, CallWriter, FinalAnswer
        └── HITLOrchestratorAgent.run()
              └── LLM이 call_outliner 호출
              └── LLM이 ask_outline_approval 호출
                    └── AskOutlineApprovalTool이 HITLData 반환 (mode="tool_result")
                    └── Agent가 hitl_interrupts 감지 → 루프 중단
        └── User approves or requests revision
        └── HITLOrchestratorAgent._resume_hitl()
              └── 승인 시: call_researcher → call_writer → final_answer
              └── 거부 시: call_outliner 재호출 (revision feedback 포함)
        └── Final Report 출력

참고:
    - BaseAgent with HITL: lecture/lec06_02_hitl/base.py
    - HITLData: lecture/lec06_02_hitl/hitl.py
    - ToolResult with hitl_data: lecture/lec06_02_hitl/tool.py
    - HITLOrchestratorAgent: lecture/lec06_02_hitl/agent.py
    - AskOutlineApprovalTool: lecture/lec06_02_hitl/ask_outline_approval.py
"""

import asyncio
import os
import sys

from lec06_02_hitl.agent import HITLOrchestratorAgent
from lec06_02_hitl.hitl import HITLData


async def main() -> None:
    """메인 데모 함수.

    HITLOrchestratorAgent를 사용하여 Report Generation Agent의
    HITL 워크플로우를 시연합니다.
    """
    print("\n" + "=" * 60)
    print("Lecture 06-02: HITL Orchestrator Agent 데모")
    print("=" * 60)

    # SERPER_API_KEY 확인
    if not os.environ.get("SERPER_API_KEY"):
        print("\n오류: SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Serper API 키는 https://serper.dev 에서 발급받을 수 있습니다.")
        print("\n사용법:")
        print("  export SERPER_API_KEY='your-api-key'")
        print("  rye run lec06-02")
        sys.exit(1)

    # 데모 주제
    user_request = "2025년 생성형 AI 시장 동향에 대한 리포트를 작성해주세요."

    print(f"\n요청: {user_request}")
    print("\nHITLOrchestratorAgent를 초기화합니다...")

    try:
        await run_hitl_orchestrator(user_request)

        print("\n" + "=" * 60)
        print("데모 완료!")
        print("=" * 60 + "\n")

    except Exception as e:
        print("\n" + "=" * 60)
        print("오류 발생")
        print("=" * 60)
        print(f"오류 메시지: {e}")
        print("\n일반적인 문제:")
        print("1. SERPER_API_KEY가 올바르게 설정되지 않음")
        print("2. 네트워크 연결 문제")
        print("3. API 할당량 초과")
        print("=" * 60 + "\n")
        sys.exit(1)


# ---------------------------------------------------------------------------
# 에이전트 실행
# ---------------------------------------------------------------------------


async def run_hitl_orchestrator(user_request: str) -> None:
    """HITLOrchestratorAgent를 실행합니다.

    사용자 요청을 받아 HITLOrchestratorAgent를 실행하며,
    아웃라인 승인(ask_outline_approval) 단계에서 HITL 인터럽트를 처리합니다.

    Args:
        user_request: 사용자의 리포트 요청
    """
    agent = await HITLOrchestratorAgent.setup(
        user_request=user_request,
        model="claude-4.5-sonnet",
        max_iterations=30,
    )

    print(f"\nRequest: {user_request}")
    print(f"Model: {agent.model}")
    print(f"Tools: {[tool.name for tool in agent.tools]}")
    print("=" * 60 + "\n")

    hitl_count = 0

    while True:
        print("-" * 60)
        print(f"Agent running (iteration: {agent.state.iteration_count + 1})...")
        print("-" * 60)

        await agent.run()

        if not agent.state.hitl_interrupts:
            print("Agent completed.\n")
            break

        hitl_count += len(agent.state.hitl_interrupts)
        print(f"\nHITL: User interaction required ({hitl_count})")
        print("-" * 60)

        process_hitl_interrupts(agent.state.hitl_interrupts)

        print("-" * 60)
        print("Resuming...\n")
        await agent._resume_hitl()  # noqa: SLF001

    # 결과 출력
    print("=" * 60)
    print("Final Report:")
    print("=" * 60)
    print_report(agent)
    print("=" * 60)

    print(f"\nPhase: {agent.state.current_phase}")
    print(f"Iterations: {agent.state.iteration_count}")
    print(f"HITL interactions: {hitl_count}")

    if agent.state.outline:
        print(f"Outline sections: {len(agent.state.outline.sections)}")
    print(f"Research sections: {len(agent.state.research_results)}")
    print(f"Reference documents: {len(agent.state.reference_documents)}")


# ---------------------------------------------------------------------------
# HITL 인터럽트 처리 함수
# ---------------------------------------------------------------------------


def process_hitl_interrupts(hitl_interrupts: list[HITLData]) -> None:
    """HITL 인터럽트를 도구 이름에 따라 적절한 핸들러로 위임합니다.

    Args:
        hitl_interrupts: 처리할 HITL 인터럽트 리스트
    """
    for hitl in hitl_interrupts:
        if hitl.tool_name == "ask_outline_approval":
            process_ask_outline_approval_interrupt(hitl)
        else:
            print(f"  Unknown HITL tool: {hitl.tool_name}\n")


def process_ask_outline_approval_interrupt(hitl: HITLData) -> None:
    """ask_outline_approval 도구의 HITL 인터럽트를 처리합니다.

    사용자에게 아웃라인을 표시하고 승인 또는 수정 요청을 받습니다.
    mode="tool_result"이므로 승인 여부와 피드백을 payload에 설정합니다.

    Args:
        hitl: 처리할 HITL 인터럽트 (mode="tool_result")
    """
    payload = hitl.payload
    outline_text: str = payload.get("outline_text", "")

    print(f"\n  Tool: {hitl.tool_name}")
    print("  Outline:")
    print("-" * 60)
    print(outline_text)
    print("-" * 60)
    print()

    while True:
        response = input("  Do you approve this outline? [y/n]: ").strip().lower()
        if response in ("y", "yes"):
            hitl.payload = {
                "outline_text": outline_text,
                "approved": True,
                "revision_feedback": "",
            }
            print("  Outline approved\n")
            break
        if response in ("n", "no"):
            print("\n  Please provide your revision feedback:")
            revision_feedback = input("  Feedback: ").strip()
            hitl.payload = {
                "outline_text": outline_text,
                "approved": False,
                "revision_feedback": revision_feedback,
            }
            print("  Outline rejected, feedback provided\n")
            break
        print("  Please enter 'y' or 'n'")


def print_report(agent: HITLOrchestratorAgent) -> None:
    """최종 리포트를 보기 좋게 출력합니다.

    Args:
        agent: HITLOrchestratorAgent 인스턴스
    """
    if not agent.state.final_report:
        print("리포트가 생성되지 않았습니다.")
        return

    report = agent.state.final_report

    print(f"\n# {report.title}\n")

    for section in report.sections:
        print(f"## {section.title}\n")
        print(section.content)
        if section.sources:
            print("\n출처:")
            for source in section.sources:
                print(f"  - {source}")
        print()

    if report.references:
        print("-" * 60)
        print("\n## 참고 문헌\n")
        for i, ref in enumerate(report.references, 1):
            print(f"  {i}. {ref}")


if __name__ == "__main__":
    asyncio.run(main())
