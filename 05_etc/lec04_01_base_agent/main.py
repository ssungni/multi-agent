"""Lecture 04-01 통합 실행 예제 - BaseAgent를 활용한 Report Outline 생성.

이 모듈은 BaseAgent의 기본 동작을 시연하는 종합 예제입니다.
SimpleAgent를 생성하고 실행하여 Agentic Loop의 전체 흐름을 보여줍니다.
Report Generation 시나리오에서 아웃라인 생성 작업을 수행합니다.

학습 포인트:
    1. Langfuse 모니터링 설정과 @observe 데코레이터 사용
       - setup_langfuse()로 트레이싱 초기화
       - Langfuse 대시보드에서 에이전트 실행 흐름 확인
    2. SimpleAgent 생성 및 초기화 (setup 패턴)
       - 비동기 팩토리 메서드 패턴 (async classmethod)
       - 상태, 도구, 설정을 한 번에 초기화
    3. Agent 실행 및 대화 이력 확인
       - run() 메서드로 Agentic Loop 시작
       - 실행 후 state.messages에서 전체 대화 흐름 확인
    4. Tool 호출 흐름 (OutlineGenerator, FinalAnswer)
       - LLM이 generate_outline 도구를 선택하여 아웃라인 생성
       - LLM이 final_answer 도구를 선택하여 결과 전달
    5. Agentic Loop의 전체 실행 흐름
       - _execute_single_step() → _call_llm() → _hook_post_llm_call() → 도구 실행

실행 방법:
    rye run python -m lec04_01_base_agent.main

아키텍처:
    User Query ("Generate an outline for a report on AI Trends")
        └── SimpleAgent.setup()
              └── BaseAgentState 초기화
              └── Tools 등록 (OutlineGeneratorTool, FinalAnswerTool)
        └── SimpleAgent.run()
              └── Agentic Loop (BaseAgent._execute_single_step)
                    ├── LLM 호출 (generate_outline tool 선택)
                    ├── Tool 실행 (아웃라인 생성)
                    ├── LLM 호출 (final_answer tool 선택)
                    └── 종료 (final_answer 감지)

참고:
    - BaseAgent: lecture/lec04_01_base_agent/base.py
    - SimpleAgent: lecture/lec04_01_base_agent/example_agent.py
    - Tools: OutlineGeneratorTool, FinalAnswerTool
"""

import asyncio
import json

from lec02_02_langfuse.observability import setup_langfuse
from lec04_01_base_agent.example_agent import SimpleAgent


async def main() -> None:
    """통합 실행 예제 메인 함수.

    이 함수는 다음 단계를 실행합니다:
    1. Langfuse 모니터링 설정
    2. SimpleAgent 생성 및 초기화
    3. Agent 실행 (Agentic Loop)
    4. 대화 이력 출력
    """
    # Step 1: Langfuse 모니터링 설정
    print("=" * 80)
    print("Setting up Langfuse monitoring...")
    print("=" * 80)
    setup_langfuse()
    print("Langfuse initialized. Check traces at: https://cloud.langfuse.com\n")

    # Step 2: SimpleAgent 생성 및 초기화
    print("=" * 80)
    print("Creating SimpleAgent...")
    print("=" * 80)
    agent = await SimpleAgent.setup(
        query="Generate an outline for a report on 'AI Trends in 2025: Agents, Multimodality, and Open Source'",
        model="claude-4.5-sonnet",
        max_iterations=5,
        stream=False,
    )
    print(f"Agent created with query: '{agent.state.messages[-1].get('content')}'")
    print(f"Model: {agent.model}")
    print(f"Max iterations: {agent.max_iterations}")
    print(f"Tools: {[tool.name for tool in agent.tools]}\n")

    # Step 3: Agent 실행
    print("=" * 80)
    print("Starting agent execution...")
    print("=" * 80)
    await agent.run()
    print("Agent execution completed.\n")

    # Step 4: 대화 이력 출력
    print("=" * 80)
    print("Conversation History:")
    print("=" * 80)
    for i, msg in enumerate(agent.state.messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        print(f"\n{i}. [{role.upper()}]")

        # Content 출력
        if isinstance(content, str):
            # 긴 내용은 잘라서 표시
            if len(content) > 500:
                print(f"{content[:500]}...")
            else:
                print(content)
        elif isinstance(content, list):
            # Content가 list인 경우 (image 등)
            for item in content:
                if isinstance(item, dict):
                    print(f"  {item.get('type', 'unknown')}: {str(item)[:200]}")
                else:
                    print(f"  {str(item)[:200]}")

        # Tool calls 출력
        tool_calls = msg.get("tool_calls")
        if tool_calls and isinstance(tool_calls, list):
            print("\n  Tool Calls:")
            for tc in tool_calls:
                if isinstance(tc, dict):
                    function = tc.get("function", {})
                    if isinstance(function, dict):
                        tool_name = function.get("name", "unknown")
                        arguments = str(function.get("arguments", ""))
                        print(f"    - Tool: {tool_name}")
                        # JSON 파싱하여 예쁘게 출력
                        try:
                            parsed_args = json.loads(arguments)
                            formatted = json.dumps(parsed_args, indent=2, ensure_ascii=False)
                            if len(formatted) > 300:
                                print(f"      Args: {formatted[:300]}...")
                            else:
                                print(f"      Args: {formatted}")
                        except (json.JSONDecodeError, TypeError):
                            if len(arguments) > 200:
                                print(f"      Args: {arguments[:200]}...")
                            else:
                                print(f"      Args: {arguments}")

        # Tool call ID 출력 (tool 응답 메시지용)
        if tool_call_id := msg.get("tool_call_id"):
            print(f"  Tool Call ID: {tool_call_id}")

    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"Total messages: {len(agent.state.messages)}")
    print(f"Iterations: {agent.state.iteration_count}")
    print("Final state: Agent stopped (final_answer tool called)")
    print("\nCheck detailed trace at: https://cloud.langfuse.com")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
