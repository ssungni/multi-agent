"""BaseAgent with Context Engineering support.

Extended from: lec08_04_cost/base.py

Changes in this version:
- Added: context_manager attribute for ContextManager integration
- Modified: _hook_pre_llm_call() to apply context processing
- Modified: _hook_pre_llm_call() to use lec08_05_02_context cache_control
"""

import asyncio
import copy
import json
from abc import ABC, abstractmethod
from typing import Any, Generic, cast, final

from langfuse.decorators import langfuse_context, observe
from litellm import (
    ChatCompletionAssistantMessage,
    ChatCompletionAssistantToolCall,
    ChatCompletionRedactedThinkingBlock,
    ChatCompletionThinkingBlock,
    ChatCompletionToolCallFunctionChunk,
    Choices,
    CustomStreamWrapper,
)
from litellm.types.completion import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolMessageParam,
)
from litellm.types.utils import ChatCompletionDeltaToolCall, ModelResponse
from typing_extensions import Self

from lec02_02_langfuse.router import router
from lec04_01_base_agent.constant import NUM_REASONING_BUDGET_TOKENS
from lec06_02_hitl.hitl import HITLData
from lec06_02_hitl.state import TState
from lec06_02_hitl.tool import BaseTool, ToolResult
from lec08_05_02_context.cache_control import apply_cache_control_blocks
from lec08_05_02_context.manager import ContextManager


class MaxIterationError(Exception):
    """에이전트가 최대 반복 횟수를 초과했을 때 발생하는 예외."""


class BaseAgent(ABC, Generic[TState]):
    """HITL 지원, 컨텍스트 관리가 포함된 모든 에이전트를 위한 기본 클래스.

    이 클래스는 다음을 포함한 핵심 에이전트 루프 기능을 제공합니다:
    - 도구 호출을 포함한 LLM 상호작용
    - 도구 실행 (병렬)
    - 상태 관리
    - HITL (Human-In-The-Loop) 지원 (lec06_02_hitl에서 추가)
    - 컨텍스트 관리 (lec08_05_context에서 추가)

    에이전트 인스턴스화에는 비동기 `setup()` 클래스 메서드를 사용합니다:
        ```python
        agent = await MyAgent.setup(state=my_state, tools=my_tools)
        result = await agent.run()
        ```

    서브클래스는 동작을 커스터마이즈하기 위해 확장 포인트 메서드를 오버라이드해야 합니다:
    - `_should_stop()`: 종료 조건 정의
    - `_hook_pre_llm_call()`: LLM 호출 전 메시지 준비
    - `_hook_post_llm_call()`: LLM 응답 처리 및 도구 실행
    - `_hook_post_step()`: 각 반복 후 후처리 작업

    도구는 자체 전/후처리를 다음을 통해 처리합니다:
    - `Tool._pre_execute_hook()`: 상태 의존적 인자 주입
    - `Tool._post_execute_hook()`: 실행 후 상태 업데이트
    """

    # 인스턴스 속성 (서브클래스 setup()에서 설정)
    state: TState
    tools: list[BaseTool]
    max_iterations: int
    model: str
    stream: bool
    context_manager: ContextManager | None = None  # [ADDED in lec08_05_context]

    @final
    def __init__(self) -> None:
        """직접 호출하지 마세요 - 대신 `await setup()` 클래스 메서드를 사용하세요."""
        self._initialized = False

    @classmethod
    @abstractmethod
    async def setup(cls, *args: Any, **kwargs: Any) -> Self:
        """새 에이전트 인스턴스를 생성하고 초기화합니다.

        에이전트를 인스턴스화하는 주요 방법입니다. __init__ 대신 이것을 사용하세요.
        서브클래스는 자체 파라미터로 이 메서드를 오버라이드하고 먼저
        `await super().setup()`을 호출한 후, 마지막에 `self._initialized = True`를 설정해야 합니다.

        의도적인 LSP 위반을 무시하려면 서브클래스 메서드 시그니처에
        `# type: ignore[override]`를 추가해야 합니다.

        Returns:
            Self: 초기화된 에이전트 인스턴스.

        Raises:
            RuntimeError: setup()이 이미 초기화된 에이전트에서 호출된 경우.
        """
        self = cls()
        if self._initialized:
            raise RuntimeError(f"{cls.__name__}.setup() called on already initialized agent")
        return self

    @observe(capture_input=True, capture_output=True)
    async def run(self) -> None:
        """메인 에이전트 실행 루프.

        `_should_stop()`이 True를 반환하거나 max_iterations에 도달할 때까지
        에이전트 루프를 실행합니다.

        Raises:
            RuntimeError: setup() 완료 전에 run()이 호출된 경우.
            MaxIterationError: max_iterations를 초과한 경우.
        """
        if not self._initialized:
            raise RuntimeError(f"{self.__class__.__name__}.run() called before setup() completed.")
        while not self._should_stop():
            self.state.iteration_count += 1
            await self._execute_single_step()

    def _should_stop(self) -> bool:
        """에이전트가 실행을 중단해야 하는지 확인합니다.

        기본 구현은 최대 반복 횟수 또는 HITL 인터럽트에서 중단합니다.
        서브클래스에서 커스텀 종료 조건을 추가하려면 오버라이드하되,
        먼저 super()._should_stop()을 호출하세요.

        Returns:
            bool: 에이전트가 중단해야 하면 True, 계속하려면 False.

        Raises:
            MaxIterationError: max_iterations를 초과한 경우.
        """
        if self.state.iteration_count >= self.max_iterations:
            raise MaxIterationError(f"Maximum iterations ({self.max_iterations}) reached")
        return bool(self.state.hitl_interrupts)

    @observe(capture_input=False, capture_output=False)
    async def _execute_single_step(self) -> None:
        """에이전트 루프의 단일 스텝을 실행합니다.

        이 메서드는:
        1. Pre-LLM 훅 호출 (메시지 준비)
        2. 도구와 함께 LLM 호출
        3. Post-LLM 훅 호출 (응답 처리, 도구 호출 실행)
        4. Post-step 훅 호출 (상태 저장 등)
        """
        # Pre-LLM 훅: 메시지 준비
        messages = await self._hook_pre_llm_call()
        # LLM 호출
        response = await self._call_llm(messages)
        # Post-LLM 훅: 응답 처리 및 도구 호출 실행
        await self._hook_post_llm_call(response)
        # Post-step 훅
        await self._hook_post_step()

    async def _hook_pre_llm_call(self) -> list[ChatCompletionMessageParam]:
        """LLM 호출 전에 실행되는 훅.

        서브클래스에서 오버라이드하여:
        - 메시지 준비 커스터마이즈 (예: 컨텍스트 크기 관리, 캐시 제어)
        - 전처리 로직 추가

        Returns:
            list: LLM에 전송할 메시지.
        """
        messages = copy.deepcopy(self.state.messages)

        # [ADDED in lec08_05_context] 컨텍스트 관리자로 처리
        if self.context_manager:
            messages = await self.context_manager.process(
                working_messages=messages,
                original_messages=self.state.messages,
            )

        # [ADDED in lec08_05_context] 캐시 제어 블록 적용
        return cast(
            list[ChatCompletionMessageParam],
            apply_cache_control_blocks(cast(list[dict[str, Any]], messages)),
        )


    async def _call_llm(
        self, messages: list[ChatCompletionMessageParam]
    ) -> ChatCompletionAssistantMessageParam:
        """LLM을 호출하고 응답 메시지를 반환합니다.

        `self.stream`에 따라 스트리밍 또는 논스트리밍 구현으로 위임합니다.

        Args:
            messages: LLM에 전송할 대화 메시지.

        Returns:
            LLM 응답 메시지.
        """
        if self.stream:
            return await self._call_llm_streaming(messages)
        return await self._call_llm_non_streaming(messages)

    async def _call_llm_non_streaming(
        self, messages: list[ChatCompletionMessageParam]
    ) -> ChatCompletionAssistantMessageParam:
        """스트리밍 없이 LLM을 호출하고 응답을 반환합니다.

        Args:
            messages: LLM에 전송할 대화 메시지.

        Returns:
            LLM 응답 메시지.
        """
        params = self._build_llm_params(messages)
        response: ModelResponse = await router.acompletion(**params, stream=False)

        message = cast(Choices, response.choices[0]).message
        return cast(ChatCompletionAssistantMessageParam, message.model_dump())

    async def _call_llm_streaming(
        self, messages: list[ChatCompletionMessageParam]
    ) -> ChatCompletionAssistantMessageParam:
        """스트리밍으로 LLM을 호출하고 전체 메시지를 조립합니다.

        응답을 스트리밍하고 조립된 메시지를 반환합니다.

        Args:
            messages: LLM에 전송할 대화 메시지.

        Returns:
            조립된 LLM 응답 메시지.
        """
        params = self._build_llm_params(messages)
        response: CustomStreamWrapper = await router.acompletion(**params, stream=True)

        # 스트리밍 청크에서 전체 메시지 조립
        message_content: str = ""
        reasoning_content: str = ""
        delta_tool_calls: list[ChatCompletionDeltaToolCall] = []
        thinking_blocks: list[
            ChatCompletionThinkingBlock | ChatCompletionRedactedThinkingBlock
        ] = []

        async for chunk in response:
            delta = chunk.choices[0].delta

            # Thinking blocks 처리 (Claude extended thinking)
            if (
                hasattr(chunk.choices[0].delta, "thinking_blocks")
                and chunk.choices[0].delta.thinking_blocks
            ):
                thinking_blocks.extend(chunk.choices[0].delta.thinking_blocks)

            # Reasoning content 처리 (Claude/Gemini extended thinking)
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                reasoning_content += cast(str, delta.reasoning_content)

            # Content 처리
            if hasattr(delta, "content") and delta.content:
                message_content += delta.content

            # Tool calls 처리
            if hasattr(delta, "tool_calls") and delta.tool_calls:
                delta_tool_calls.extend(delta.tool_calls)

        merged_thinking_blocks = self._merge_delta_thinking_blocks(thinking_blocks)
        merged_tool_calls = self._merge_delta_tool_calls(delta_tool_calls)

        # ChatCompletionAssistantMessage로 메시지 빌드 (모든 메타데이터 보존)
        message = ChatCompletionAssistantMessage(
            role="assistant",
            content=message_content,
            reasoning_content=reasoning_content if reasoning_content else None,
            tool_calls=merged_tool_calls,
            thinking_blocks=merged_thinking_blocks,
        )

        return cast(ChatCompletionAssistantMessageParam, message)

    def _build_llm_params(self, messages: list[ChatCompletionMessageParam]) -> dict[str, Any]:
        """LLM 호출을 위한 공통 파라미터를 빌드합니다.

        Args:
            messages: LLM에 전송할 대화 메시지.

        Returns:
            router.acompletion을 위한 파라미터 딕셔너리.
        """
        is_claude = "claude" in self.model.lower()
        extra_headers = (
            {"anthropic-beta": "context-1m-2025-08-07,interleaved-thinking-2025-05-14"}
            if is_claude
            else None
        )
        tool_choice = None if is_claude else "required"

        return {
            "messages": messages,
            "model": self.model,
            "tools": [tool.to_chat_completion_tool() for tool in self.tools],
            "thinking": {
                "type": "enabled",
                "budget_tokens": NUM_REASONING_BUDGET_TOKENS,
            },
            "max_tokens": 50000,
            "extra_headers": extra_headers,
            "tool_choice": tool_choice,
            "metadata": {
                "existing_trace_id": langfuse_context.get_current_trace_id(),
                "parent_observation_id": langfuse_context.get_current_observation_id(),
            },
        }

    @staticmethod
    def _merge_delta_thinking_blocks(
        delta_thinking_blocks: list[
            ChatCompletionThinkingBlock | ChatCompletionRedactedThinkingBlock
        ],
    ) -> list[ChatCompletionThinkingBlock | ChatCompletionRedactedThinkingBlock]:
        """스트리밍 thinking block 델타를 완전한 thinking blocks로 병합합니다.

        Args:
            delta_thinking_blocks: 스트리밍 청크의 thinking block 델타 리스트.

        Returns:
            병합된 thinking blocks 리스트 (redacted blocks 제외).
        """
        merged_block: ChatCompletionThinkingBlock = ChatCompletionThinkingBlock(
            type="thinking",
            thinking="",
            signature="",
        )

        for delta_block in delta_thinking_blocks:
            if delta_block.get("type") == "redacted":
                continue
            delta_block = cast(ChatCompletionThinkingBlock, delta_block)

            if thinking := delta_block.get("thinking", ""):
                merged_block["thinking"] += thinking
            if signature := delta_block.get("signature", ""):
                merged_block["signature"] = signature

        return [merged_block] if merged_block["thinking"] else []

    @staticmethod
    @observe(capture_input=False, capture_output=False)
    def _merge_delta_tool_calls(
        delta_tool_calls: list[ChatCompletionDeltaToolCall],
    ) -> list[ChatCompletionAssistantToolCall]:
        """스트리밍 tool call 델타를 완전한 tool calls로 병합합니다.

        스트리밍 응답은 tool call을 여러 청크로 분할합니다.
        이 메서드는 이를 완전한 tool call 객체로 다시 조립합니다.

        Args:
            delta_tool_calls: 스트리밍 청크의 tool call 델타 리스트.

        Returns:
            병합된 tool call 딕셔너리 리스트.
        """
        if not delta_tool_calls:
            return []

        merged_calls: dict[int, ChatCompletionAssistantToolCall] = {}
        for delta_call in delta_tool_calls:
            index = delta_call.index
            if index not in merged_calls:
                merged_calls[index] = ChatCompletionAssistantToolCall(
                    id=delta_call.id,
                    type="function",
                    function=ChatCompletionToolCallFunctionChunk(
                        name=delta_call.function.name,
                        arguments=delta_call.function.arguments,
                    ),
                )

            merged_call = merged_calls[index]

            if delta_call.id is not None:
                merged_call["id"] = delta_call.id

            if delta_call.function and delta_call.function.name is not None:
                merged_call["function"]["name"] = delta_call.function.name

            if delta_call.function and delta_call.function.arguments is not None:
                merged_call["function"]["arguments"] += delta_call.function.arguments

        return [merged_calls[k] for k in sorted(merged_calls)]

    async def _hook_post_llm_call(self, message: ChatCompletionAssistantMessageParam) -> None:
        """LLM 호출 후에 실행되는 훅.

        LLM 응답을 처리하고 메시지를 상태에 추가하며 도구 호출을 실행합니다.
        서브클래스에서 super() 호출 전에 전처리를 추가하려면 오버라이드하세요.

        Args:
            message: 응답의 LLM 메시지 객체.
        """
        self._append_message(message)

        # 도구 호출이 있으면 실행
        if tool_calls := message.get("tool_calls", []):
            tool_messages, hitl_interrupts = await self._execute_tool_calls(list(tool_calls))
            self._extend_messages(tool_messages)
            self.state.hitl_interrupts = hitl_interrupts
        else:
            # LLM이 도구를 호출하지 않으면 오류 메시지 주입
            self._append_message(
                {
                    "role": "user",
                    "content": (
                        "<SYSTEM_ERROR>"
                        "CRITICAL: You MUST call a tool. "
                        "You are NOT allowed to respond without selecting a tool. "
                        "Your ONLY capability is to select and execute tools. "
                        "Direct text responses without tool calls are FORBIDDEN. "
                        "Select an appropriate tool NOW."
                        "</SYSTEM_ERROR>"
                    ),
                }
            )

    @observe(name="step_execute_tool_calls", capture_input=True, capture_output=True)
    @final
    async def _execute_tool_calls(
        self, tool_calls: list[ChatCompletionMessageToolCallParam]
    ) -> tuple[list[ChatCompletionToolMessageParam], list[HITLData]]:
        """여러 도구 호출을 병렬로 실행합니다.

        Args:
            tool_calls: LLM 응답의 도구 호출 리스트.

        Returns:
            tuple: (tool_messages, hitl_interrupts)
                - tool_messages: 도구 응답 메시지 리스트
                - hitl_interrupts: HITL 인터럽트 데이터 리스트 (있는 경우)
        """
        tool_messages: list[ChatCompletionToolMessageParam] = []
        hitl_interrupts: list[HITLData] = []

        # 병렬 실행 태스크 빌드
        tool_execution_tasks = [
            self._tool_call(
                tool_call.get("id", ""),
                tool_call["function"]["name"],
                json.loads(tool_call["function"]["arguments"]),
            )
            for tool_call in tool_calls
            if tool_call and tool_call["function"]["name"]
        ]

        # 병렬 실행
        tool_results = await asyncio.gather(*tool_execution_tasks)

        for tool_call, result in zip(tool_calls, tool_results):
            if result.hitl_data:
                # LLM 응답의 tool_call_id를 hitl_data에 주입
                result.hitl_data.tool_call_id = tool_call.get("id") or ""
                hitl_interrupts.append(result.hitl_data)
            else:
                tool_messages.append(self._build_tool_message(tool_call, result))

        return tool_messages, hitl_interrupts

    async def _tool_call(
        self, tool_call_id: str, name: str, arguments: dict[str, Any]
    ) -> ToolResult:
        """단일 도구 호출을 실행합니다.

        Args:
            tool_call_id: LLM 응답의 도구 호출 ID.
            name: 실행할 도구 이름.
            arguments: 도구에 전달할 인자.

        Returns:
            ToolResult: 도구 실행 결과.
        """
        tool = self._find_tool_by_name(name)
        if not tool:
            return ToolResult(content=f"Tool {name} not found", artifact=None)

        try:
            return await tool.call(
                state=self.state,
                tool_call_id=tool_call_id,
                arguments=arguments,
            )
        except Exception as e:
            return ToolResult(content=str(e), artifact=None)

    def _find_tool_by_name(self, name: str) -> BaseTool | None:
        """이름으로 도구를 찾습니다.

        Args:
            name: 찾을 도구 이름.

        Returns:
            도구 인스턴스 또는 찾지 못하면 None.
        """
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    @final
    def _build_tool_message(
        self, tool_call: ChatCompletionMessageToolCallParam, result: ToolResult
    ) -> ChatCompletionToolMessageParam:
        """도구 호출과 결과로 도구 메시지를 빌드합니다.

        Args:
            tool_call: LLM의 원본 도구 호출.
            result: 도구 실행 결과.

        Returns:
            ChatCompletionToolMessageParam: 포맷팅된 도구 메시지.
        """
        return ChatCompletionToolMessageParam(
            role="tool",
            content=result.content,
            tool_call_id=tool_call.get("id") or "",
        )

    async def _hook_post_step(self) -> None:
        """각 스텝 완료 후에 실행되는 훅.

        서브클래스에서 후처리 작업을 위해 오버라이드합니다:
        - 스토리지에 상태 저장
        - 로깅 또는 모니터링
        """

    def _append_message(self, message: ChatCompletionMessageParam) -> None:
        """state.messages에 메시지를 추가합니다.

        Args:
            message: 추가할 메시지.
        """
        self.state.messages.append(message)

    def _extend_messages(self, messages: list[ChatCompletionMessageParam]) -> None:
        """state.messages에 여러 메시지를 확장합니다.

        Args:
            messages: 추가할 메시지들.
        """
        self.state.messages.extend(messages)

    @observe(capture_input=False, capture_output=False)
    async def _resume_hitl(self) -> None:
        """HITL 인터럽트에서 사용자 응답으로 에이전트 실행을 재개합니다.

        이 메서드는 사용자가 HITL 인터럽트에 응답한 후 호출됩니다.
        사용자의 응답을 처리하고 에이전트 실행을 계속합니다.

        이 메서드는 세 가지 HITL 모드를 처리합니다:
        1. rejected=True: 사용자가 도구 호출을 거부함 - 거부 메시지 주입
        2. mode="tool_call": 사용자 응답을 포함하여 도구 재실행
        3. mode="tool_result": 사용자가 결과를 직접 제공함 - 도구 메시지로 주입

        Raises:
            Exception: HITL 인터럽트가 없거나 중첩 HITL이 감지된 경우
        """
        if not self.state.hitl_interrupts:
            raise Exception("No HITL interrupt found in state")

        tool_calls: list[ChatCompletionMessageToolCallParam] = []
        tool_messages: list[ChatCompletionToolMessageParam] = []

        for hitl_data in self.state.hitl_interrupts:
            if hitl_data.rejected:
                # 사용자가 거부함 - 거부 메시지 주입
                tool_messages.append(
                    ChatCompletionToolMessageParam(
                        role="tool",
                        content=f"User rejected the {hitl_data.tool_name} operation",
                        tool_call_id=hitl_data.tool_call_id,
                    )
                )
            elif hitl_data.mode == "tool_call":
                # tool_call 모드: 사용자 응답을 포함하여 도구 재실행
                tool_calls.append(
                    ChatCompletionMessageToolCallParam(
                        id=hitl_data.tool_call_id,
                        type="function",
                        function={
                            "name": hitl_data.tool_name,
                            "arguments": json.dumps(hitl_data.payload),
                        },
                    )
                )
            elif hitl_data.mode == "tool_result":
                # 사용자가 결과를 직접 제공함 - 도구 메시지로 주입
                tool_message = ChatCompletionToolMessageParam(
                    role="tool",
                    content=json.dumps(hitl_data.payload),
                    tool_call_id=hitl_data.tool_call_id,
                )
                tool_messages.append(tool_message)

        # 도구 호출 실행 (tool_call 모드용)
        if tool_calls:
            tool_results, nested_hitl_interrupts = await self._execute_tool_calls(tool_calls)
            if nested_hitl_interrupts:
                raise Exception(f"Nested HITL not supported: {nested_hitl_interrupts[0].tool_name}")
            tool_messages.extend(tool_results)

        # 모든 도구 메시지를 상태에 추가
        self._extend_messages(list(tool_messages))
        # HITL 인터럽트 초기화
        self.state.hitl_interrupts = []
