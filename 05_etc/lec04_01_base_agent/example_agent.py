"""BaseAgent 사용법을 보여주는 예제 에이전트 구현.

이 예제는 Report Generation 컨텍스트에서 다음을 보여줍니다:
1. BaseAgent 확장
2. setup() 클래스 메서드 구현
3. 커스텀 도구 정의 (아웃라인 생성 도구)
4. 에이전트 루프 실행

Report Generation Agent 시스템에서 가장 기본적인 단위인
아웃라인 생성을 간소화하여 BaseAgent 패턴의 핵심 동작을 시연합니다.
"""

import asyncio
import json
from typing import Any

from typing_extensions import Self

from lec04_01_base_agent.base import BaseAgent
from lec04_01_base_agent.state import BaseAgentState
from lec04_01_base_agent.tool import BaseTool, ToolResult


class OutlineGeneratorTool(BaseTool[BaseAgentState]):
    """리포트 아웃라인을 생성하는 도구.

    주어진 주제에 대해 구조화된 아웃라인을 생성합니다.
    lec05_01_outliner의 GenerateOutlineTool을 단순화한 학습용 버전입니다.

    학습 포인트:
        - BaseTool의 name, description, parameters 정의 방법
        - JSON Schema를 사용한 파라미터 스키마 정의
        - _execute 메서드 구현 패턴
    """

    name = "generate_outline"
    description = (
        "Generate a structured report outline for the given topic. "
        "Provide a title and sections with descriptions. "
        "Use this tool to create the outline, then use final_answer to deliver it."
    )
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the report outline",
            },
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Section title"},
                        "description": {
                            "type": "string",
                            "description": "Brief description of what this section covers",
                        },
                    },
                    "required": ["title", "description"],
                    "additionalProperties": False,
                },
                "description": "List of sections with title and description",
            },
        },
        "required": ["title", "sections"],
        "additionalProperties": False,
    }

    async def _execute(self, state: BaseAgentState, **kwargs: Any) -> ToolResult:
        """아웃라인을 생성하고 포맷팅하여 반환합니다.

        Args:
            state: 현재 에이전트 상태 (이 도구에서는 사용하지 않음)
            **kwargs: title (str), sections (list[dict])

        Returns:
            생성된 아웃라인을 포맷팅한 ToolResult
        """
        _ = state  # 이 도구에서는 상태를 사용하지 않음
        title: str = kwargs["title"]
        sections: list[dict[str, str]] = kwargs["sections"]

        # 아웃라인 포맷팅
        lines = [f"Report Outline: {title}\n"]
        for i, section in enumerate(sections, 1):
            lines.append(f"{i}. {section['title']}")
            lines.append(f"   Description: {section['description']}")
            lines.append("")

        formatted_outline = "\n".join(lines)

        return ToolResult(
            content=formatted_outline,
            artifact={"title": title, "sections": sections, "section_count": len(sections)},
        )


class FinalAnswerTool(BaseTool[BaseAgentState]):
    """최종 답변을 제공하고 대화를 종료하는 도구.

    에이전트가 작업을 완료했을 때 최종 결과를 사용자에게 전달하고
    Agentic Loop를 종료하는 역할을 합니다.

    학습 포인트:
        - 에이전트의 종료 조건으로 사용되는 도구 패턴
        - _should_stop()과 연계하여 루프 종료 제어
    """

    name = "final_answer"
    description = "Provide the final answer to the user's question. Use this when you have completed the task."
    parameters = {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "The final answer to provide to the user",
            },
        },
        "required": ["answer"],
        "additionalProperties": False,
    }

    async def _execute(self, state: BaseAgentState, **kwargs: Any) -> ToolResult:
        """답변을 최종으로 표시합니다."""
        _ = state  # 이 도구에서는 상태를 사용하지 않음
        answer: str = kwargs["answer"]
        return ToolResult(content=f"Final answer: {answer}", artifact={"is_final": True})


class SimpleAgent(BaseAgent[BaseAgentState]):
    """Report Outline 생성을 위한 간단한 에이전트 구현.

    BaseAgent 패턴의 핵심 동작을 시연하는 예제 에이전트입니다.
    사용자가 요청한 주제에 대해 아웃라인을 생성하고 최종 답변을 제공합니다.

    Agentic Loop 흐름:
        1. LLM이 generate_outline 도구를 호출하여 아웃라인 생성
        2. LLM이 final_answer 도구를 호출하여 결과 전달
        3. _should_stop()이 final_answer 감지 시 루프 종료

    학습 포인트:
        - setup() 패턴을 통한 비동기 초기화
        - _should_stop() 오버라이드를 통한 종료 조건 정의
    """

    @classmethod
    async def setup(  # type: ignore[override]
        cls,
        query: str,
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 5,
        stream: bool = False,
    ) -> Self:
        """새 SimpleAgent 인스턴스를 생성합니다.

        Args:
            query: 처리할 사용자 쿼리 (리포트 주제)
            model: 사용할 LLM 모델
            max_iterations: 최대 반복 횟수
            stream: 스트리밍 사용 여부

        Returns:
            초기화된 SimpleAgent 인스턴스
        """
        self = await super().setup()

        # 상태 초기화
        self.state = BaseAgentState(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a report outline generation assistant. "
                        "When the user provides a topic, use the generate_outline tool "
                        "to create a structured outline with 3-5 sections. "
                        "After generating the outline, use the final_answer tool "
                        "to deliver a summary of the outline to the user."
                    ),
                },
                {"role": "user", "content": query},
            ],
        )

        # 에이전트 속성 설정
        self.tools = [OutlineGeneratorTool(), FinalAnswerTool()]
        self.max_iterations = max_iterations
        self.model = model
        self.stream = stream

        self._initialized = True
        return self

    def _should_stop(self) -> bool:
        """final_answer 도구가 사용되거나 최대 반복 횟수에 도달하면 중단합니다."""
        # 부모 클래스 조건 먼저 확인 (최대 반복 횟수)
        if super()._should_stop():
            return True

        # final_answer가 호출되었는지 확인
        for message in reversed(self.state.messages):
            if message.get("role") == "tool":
                content = message.get("content", "")
                if isinstance(content, str) and "Final answer:" in content:
                    return True
        return False


async def main() -> None:
    """간단한 예제를 실행합니다."""
    # 에이전트 생성 및 실행
    agent = await SimpleAgent.setup(
        query="Generate an outline for a report on 'AI Trends in 2025'",
        model="claude-4.5-sonnet",
        max_iterations=5,
        stream=False,
    )

    print("Starting agent execution...\n")
    await agent.run()

    print("\n" + "=" * 80)
    print("Conversation history:")
    print("=" * 80)
    for i, msg in enumerate(agent.state.messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        print(f"\n{i}. [{role.upper()}]")
        if isinstance(content, str):
            print(content[:500])  # 긴 내용은 잘라서 표시
        tool_calls = msg.get("tool_calls")
        if tool_calls and isinstance(tool_calls, list):
            for tc in tool_calls:
                if isinstance(tc, dict):
                    func = tc.get("function", {})
                    if isinstance(func, dict):
                        print(f"   Tool: {func.get('name', 'unknown')}")
                        args = func.get("arguments", "")
                        # JSON 파싱하여 예쁘게 출력
                        try:
                            parsed_args = json.loads(str(args))
                            print(f"   Args: {json.dumps(parsed_args, indent=2)[:300]}")
                        except (json.JSONDecodeError, TypeError):
                            print(f"   Args: {str(args)[:200]}")


if __name__ == "__main__":
    asyncio.run(main())
