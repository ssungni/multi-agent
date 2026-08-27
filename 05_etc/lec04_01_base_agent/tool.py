"""에이전트 도구 인터페이스 모듈.

에이전트가 외부 시스템 및 API와 상호작용할 수 있게 해주는 핵심 도구 추상화를 정의합니다.
도구는 에이전트가 텍스트 생성을 넘어서 동작을 수행하는 주요 메커니즘입니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic

from langfuse.decorators import langfuse_context, observe
from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk
from pydantic import BaseModel

from lec04_01_base_agent.state import TState


class ToolResult(BaseModel):
    """도구 실행 결과.

    Attributes:
        content: LLM에 도구 출력으로 반환되는 문자열 결과.
            대화 이력에 도구 메시지로 나타납니다.
        artifact: 에이전트가 프로그래밍 방식으로 사용하기 위한 선택적 구조화 데이터.
            content(LLM용)와 달리 artifact는 에이전트 코드가 직접 사용할 수 있는
            데이터를 저장합니다 (예: 파싱된 객체, 메타데이터).
    """

    content: str
    artifact: Any = None


class BaseTool(ABC, Generic[TState]):
    """모든 에이전트 도구의 기본 클래스.

    도구는 에이전트의 기능을 확장하여 외부 시스템과 상호작용하고,
    데이터베이스를 쿼리하고, 계산을 수행하는 등의 작업을 할 수 있게 합니다.

    각 도구는 다음을 정의합니다:
    - LLM이 언제 사용할지 이해할 수 있는 이름과 설명
    - 파라미터를 위한 JSON 스키마 (LLM이 유효한 호출을 생성하는 데 사용)
    - ToolResult를 반환하는 실행 로직

    도구 생명주기:
    1. LLM이 이름/설명을 기반으로 도구 호출을 결정
    2. 에이전트가 _pre_execute_hook을 호출하여 상태 의존적 인자를 주입
    3. 도구가 _execute 메서드를 통해 실행
    4. 에이전트가 _post_execute_hook을 호출하여 결과에 따라 상태 업데이트

    Type Parameters:
        TState: 이 도구가 작동하는 에이전트 상태 타입
    """

    # 도구 정의 - 서브클래스에서 반드시 설정해야 함
    name: str
    description: str
    parameters: dict[str, Any]
    strict: bool = True  # OpenAI strict 모드 (파라미터 검증용)

    @observe(capture_input=False, capture_output=False)
    async def call(
        self,
        state: TState,
        tool_call_id: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """도구를 실행합니다.

        @observe 데코레이터는 각 도구 호출에 대한 Langfuse 모니터링을 활성화하여
        도구 사용, 지연 시간, 오류에 대한 가시성을 제공합니다.

        Args:
            state: 현재 에이전트 상태
            tool_call_id: LLM 응답의 도구 호출 ID
            arguments: LLM에서 전달된 인자

        Returns:
            도구 실행의 ToolResult

        Raises:
            Exception: 도구 실행 실패 시 도구 컨텍스트와 함께 래핑됨
        """
        langfuse_context.update_current_observation(
            name=self.name,
        )

        try:
            result = await self._execute(state, tool_call_id=tool_call_id, **arguments)

            if not isinstance(result, ToolResult):
                raise TypeError(
                    f"Tool {self.name} returned {type(result).__name__}, expected ToolResult"
                )

            return result

        except Exception as e:
            raise Exception(f"Error calling tool {self.name}: {e}") from e

    @abstractmethod
    async def _execute(self, state: TState, **kwargs: Any) -> ToolResult:
        """도구의 핵심 로직을 실행합니다.

        도구 구현의 메인 진입점입니다. 서브클래스는 반드시 이 메서드를
        자체 로직으로 구현해야 합니다.

        Args:
            state: 현재 에이전트 상태
            **kwargs: LLM에서 전달된 도구별 인자 (tool_call_id 포함)

        Returns:
            실행 결과를 담은 ToolResult
        """

    def to_chat_completion_tool(self) -> ChatCompletionToolParam:
        """도구를 LiteLLM 형식으로 변환합니다.

        LLM이 어떤 도구가 사용 가능하고 어떻게 호출하는지 이해하는 데 사용되는
        JSON 구조를 생성합니다.

        Returns:
            LiteLLM의 completion API와 호환되는 ChatCompletionToolParam
        """
        return ChatCompletionToolParam(
            type="function",
            function=ChatCompletionToolParamFunctionChunk(
                name=self.name,
                description=self.description,
                parameters=self.parameters,
                strict=self.strict,
            ),
        )

