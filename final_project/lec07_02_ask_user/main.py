"""Lecture 07-02 통합 실행 예제 - 두 가지 HITL 모드가 공존하는 Report Generation Agent.

이 모듈은 두 가지 HITL 도구가 공존하는 Report Generation Agent를 시연합니다:
1. ask_user_question (mode="tool_call"): 모호한 사용자 요청을 명확화
2. ask_outline_approval (mode="tool_result"): 아웃라인 승인/수정 요청

학습 포인트:
    1. 두 가지 HITL 모드의 공존
       - tool_call 모드: 사용자 답변을 받아 도구를 재실행
       - tool_result 모드: 사용자가 직접 결과(승인/거부)를 제공
    2. HITL 인터럽트 처리 분기
       - hitl.tool_name으로 분기하여 각 도구에 맞는 처리
    3. ExtendedBaseAgent의 _resume_hitl()
       - tool_call 모드: 도구 재실행 후 결과 주입
       - tool_result 모드: payload를 JSON으로 주입 (기존 방식)

실행 방법:
    rye run lec07-02

HITL 흐름:
    User Query ("AI에 대한 리포트를 작성해줘") — 의도적으로 모호함
        └── ReportAgent.setup()
              └── Tools: AskUserQuestion, CallOutliner, AskOutlineApproval,
                         CallResearcher, CallWriter, FinalAnswer
        └── ReportAgent.run()
              └── LLM이 ask_user_question 호출 (어떤 AI? 범위? 대상?)
                    └── HITL interrupt (mode="tool_call") → Agent 일시정지
        └── User answers (e.g., "생성형 AI", "시장 동향", "2025년")
        └── _resume_hitl() → ask_user_question 재실행 → Q&A content 반환
        └── ReportAgent.run() 재개
              └── LLM이 call_outliner(clarified topic) 호출
              └── LLM이 ask_outline_approval(outline_text) 호출
                    └── HITL interrupt (mode="tool_result") → Agent 일시정지
        └── User approves
        └── _resume_hitl() → payload를 JSON으로 주입
        └── ReportAgent.run() 재개
              └── call_researcher → call_writer → final_answer → COMPLETE
"""

import asyncio
import os
import sys
from typing import Any

from langfuse.decorators import observe
from typing_extensions import Self

from lec02_02_langfuse.observability import setup_langfuse
from lec05_01_outliner.agent import OutlinerAgent
from lec05_02_researcher.agent import ResearcherWorkflow
from lec05_03_writer.agent import WriterAgent
from lec06_01_orchestrator.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from lec06_01_orchestrator.tools import (
    CallOutlinerTool,
    CallResearcherTool,
    CallWriterTool,
    FinalAnswerTool,
)
from lec06_02_hitl.ask_outline_approval import AskOutlineApprovalTool
from lec06_02_hitl.state import HITLPhase
from lec07_02_ask_user.ask_user import AskUserQuestionTool
from lec07_02_ask_user.base import ExtendedBaseAgent
from lec07_02_ask_user.hitl import ExtendedHITLData
from lec07_02_ask_user.state import ExtendedOrchestratorState

# ---------------------------------------------------------------------------
# 시스템 프롬프트 확장
# ---------------------------------------------------------------------------

REPORT_AGENT_SYSTEM_PROMPT = (
    ORCHESTRATOR_SYSTEM_PROMPT
    + """

## Additional Instructions for User Interaction

- If the user's request is vague or ambiguous (e.g., "write a report about AI"),
  use `ask_user_question` FIRST to clarify the topic before generating an outline.
  Ask about: specific subtopic, scope, target audience, time period, etc.
- After generating an outline with `call_outliner`, ALWAYS use `ask_outline_approval`
  to get user approval before proceeding to research.
- If the user rejects the outline, incorporate their feedback and regenerate with `call_outliner`.
"""
)

# ---------------------------------------------------------------------------
# Report Agent
# ---------------------------------------------------------------------------


class ReportAgent(ExtendedBaseAgent[ExtendedOrchestratorState]):
    """두 가지 HITL 모드를 지원하는 Report Generation Agent.

    ExtendedBaseAgent를 상속하여 tool_call 모드와 tool_result 모드를
    모두 처리할 수 있습니다.

    도구 사용 순서:
    1. AskUserQuestionTool: 모호한 요청 명확화 (tool_call 모드)
    2. CallOutlinerTool: 아웃라인 생성
    3. AskOutlineApprovalTool: 아웃라인 승인 (tool_result 모드)
    4. CallResearcherTool: 섹션별 리서치
    5. CallWriterTool: 최종 리포트 작성
    6. FinalAnswerTool: 결과 전달
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        user_request: str,
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 30,
    ) -> Self:
        """새 ReportAgent 인스턴스를 생성하고 초기화합니다.

        Args:
            user_request: 사용자의 리포트 요청
            model: 사용할 LLM 모델 이름
            max_iterations: 최대 반복 횟수

        Returns:
            초기화된 ReportAgent 인스턴스
        """
        self = await super().setup()

        self.state = ExtendedOrchestratorState(
            model=model,
            original_request=user_request,
            messages=[
                {"role": "system", "content": REPORT_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_request},
            ],
        )

        # AskUserQuestionTool/AskOutlineApprovalTool은 lec06_02_hitl.tool.BaseTool,
        # 나머지는 lec04_01_base_agent.tool.BaseTool을 상속합니다.
        # 두 BaseTool은 동일한 인터페이스의 별도 구현체이므로 런타임에서 호환됩니다.
        tools: list[Any] = [
            AskUserQuestionTool(),
            CallOutlinerTool(subagent_class=OutlinerAgent),
            AskOutlineApprovalTool(),
            CallResearcherTool(workflow_class=ResearcherWorkflow),
            CallWriterTool(subagent_class=WriterAgent),
            FinalAnswerTool(),
        ]
        self.tools = tools
        self.max_iterations = max_iterations
        self.model = model
        self.stream = True

        self._initialized = True
        return self

    def _should_stop(self) -> bool:
        """워크플로우 완료 시 에이전트를 중단합니다."""
        if super()._should_stop():
            return True
        return self.state.current_phase == HITLPhase.COMPLETE


# ---------------------------------------------------------------------------
# HITL 인터럽트 처리 함수
# ---------------------------------------------------------------------------


def get_single_answer(question: dict, tool_name: str) -> str:
    """단일 질문에 대한 사용자 답변을 받습니다.

    Args:
        question: 질문 딕셔너리 (question, header, multiSelect, options 포함)
        tool_name: 도구 이름 (표시용)

    Returns:
        사용자가 선택한 답변
    """
    question_text = question.get("question", "")
    header = question.get("header", "")
    multi_select = question.get("multiSelect", False)
    options = question.get("options", [])

    print(f"\n  Tool: {tool_name}")
    print(f"  {header}: {question_text}")
    print()

    for idx, option in enumerate(options, 1):
        label = option.get("label", "")
        description = option.get("description", "")
        print(f"  {idx}. {label}")
        print(f"     {description}")

    print(f"  {len(options) + 1}. Other (custom text input)")
    print()

    if multi_select:
        print("  Select one or more options (comma-separated, e.g., '1,2'):")
    else:
        print("  Select an option:")

    while True:
        response = input("  Your choice: ").strip()

        if response == str(len(options) + 1):
            custom_input = input("  Enter your custom response: ").strip()
            if custom_input:
                return custom_input
            print("  Please enter a non-empty response")
            continue

        if multi_select and "," in response:
            try:
                indices = [int(x.strip()) for x in response.split(",")]
                if all(1 <= idx <= len(options) for idx in indices):
                    selected_labels = [options[idx - 1].get("label", "") for idx in indices]
                    return ", ".join(selected_labels)
            except ValueError:
                pass
            print(f"  Please enter valid option numbers (1-{len(options)})")
        else:
            try:
                idx = int(response)
                if 1 <= idx <= len(options):
                    return options[idx - 1].get("label", "")
            except ValueError:
                pass
            print(f"  Please enter a valid option number (1-{len(options) + 1})")


def get_user_answers(hitl: ExtendedHITLData) -> list[str]:
    """ask_user_question 도구의 HITL 인터럽트를 처리합니다.

    모든 질문에 대해 사용자 답변을 수집합니다.

    Args:
        hitl: 처리할 HITL 인터럽트 (mode="tool_call")

    Returns:
        각 질문에 대한 사용자 답변 리스트
    """
    payload = hitl.payload
    questions = payload.get("questions", [])

    if not questions:
        return []

    answers: list[str] = []
    for question in questions:
        answer = get_single_answer(question, hitl.tool_name)
        answers.append(answer)

    return answers


def process_ask_outline_approval_interrupt(hitl: ExtendedHITLData) -> None:
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


def process_hitl_interrupts(hitl_interrupts: list[ExtendedHITLData]) -> None:
    """HITL 인터럽트를 도구 이름에 따라 적절한 핸들러로 위임합니다.

    - ask_user_question (tool_call 모드): 사용자 답변을 payload["answers"]에 설정
    - ask_outline_approval (tool_result 모드): 승인/거부를 payload에 설정

    Args:
        hitl_interrupts: 처리할 HITL 인터럽트 리스트
    """
    for hitl in hitl_interrupts:
        if hitl.tool_name == "ask_user_question":
            answers = get_user_answers(hitl)
            if answers:
                hitl.payload["answers"] = answers
                print(f"  User answered: {answers}\n")
            else:
                hitl.rejected = True
                print("  No answer provided\n")
        elif hitl.tool_name == "ask_outline_approval":
            process_ask_outline_approval_interrupt(hitl)
        else:
            print(f"  Unknown HITL tool: {hitl.tool_name}\n")


# ---------------------------------------------------------------------------
# 리포트 출력
# ---------------------------------------------------------------------------


def print_report(agent: ReportAgent) -> None:
    """최종 리포트를 보기 좋게 출력합니다.

    Args:
        agent: ReportAgent 인스턴스
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


# ---------------------------------------------------------------------------
# 에이전트 실행
# ---------------------------------------------------------------------------


async def run_report_agent(user_request: str) -> None:
    """ReportAgent를 실행합니다.

    사용자 요청을 받아 ReportAgent를 실행하며,
    ask_user_question과 ask_outline_approval 두 HITL 인터럽트를 모두 처리합니다.

    Args:
        user_request: 사용자의 리포트 요청
    """
    agent = await ReportAgent.setup(
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
# 메인
# ---------------------------------------------------------------------------


async def main() -> None:
    """통합 실행 예제 메인 함수.

    두 가지 HITL 모드(tool_call, tool_result)가 공존하는
    Report Generation Agent 워크플로우를 시연합니다.
    """
    setup_langfuse()

    print("\n" + "=" * 60)
    print("Lecture 07-02: Report Agent with Dual HITL Modes")
    print("=" * 60)

    # SERPER_API_KEY 확인
    if not os.environ.get("SERPER_API_KEY"):
        print("\n오류: SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Serper API 키는 https://serper.dev 에서 발급받을 수 있습니다.")
        print("\n사용법:")
        print("  export SERPER_API_KEY='your-api-key'")
        print("  rye run lec07-02")
        sys.exit(1)

    # 의도적으로 모호한 사용자 요청 → ask_user_question 유발
    user_request = "AI에 대한 리포트를 작성해줘"

    print(f"\n요청: {user_request}")
    print("\nReportAgent를 초기화합니다...")

    try:
        await run_report_agent(user_request)

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


if __name__ == "__main__":
    asyncio.run(main())
