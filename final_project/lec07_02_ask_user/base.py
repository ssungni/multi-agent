"""tool_call 모드를 지원하는 확장된 기본 에이전트.

lec06_02_hitl.base.BaseAgent를 상속하여 _resume_hitl()을 오버라이드합니다.
- tool_result 모드: 기존과 동일 (payload를 JSON으로 tool message에 주입)
- tool_call 모드: _execute_tool_calls()로 도구 재실행
"""

import json

from langfuse.decorators import observe
from litellm.types.completion import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolMessageParam,
)

from lec06_02_hitl.base import BaseAgent
from lec07_02_ask_user.hitl import ExtendedHITLData
from lec07_02_ask_user.state import TExtendedState


class ExtendedBaseAgent(BaseAgent[TExtendedState]):  # type: ignore[type-var]
    """tool_call 모드를 지원하는 확장된 기본 에이전트.

    _resume_hitl()을 오버라이드하여 tool_call 모드를 처리합니다:
    - tool_result 모드: payload를 JSON으로 tool message에 주입 (기존 동작)
    - tool_call 모드: _execute_tool_calls()로 도구를 재실행하여 결과를 tool message로 주입

    _hook_post_llm_call()을 오버라이드하여 부모의 _execute_tool_calls()에서 수집된
    HITLData를 ExtendedHITLData로 변환합니다.
    """

    async def _hook_post_llm_call(self, message: ChatCompletionAssistantMessageParam) -> None:
        """LLM 호출 후 실행되는 훅 - HITLData를 ExtendedHITLData로 변환합니다.

        부모의 _hook_post_llm_call()을 호출한 뒤,
        state.hitl_interrupts에 저장된 HITLData를 ExtendedHITLData로 변환합니다.
        """
        await super()._hook_post_llm_call(message)

        if self.state.hitl_interrupts:
            extended_interrupts: list[
                ExtendedHITLData
            ] = []  # [ADDED in lec07_02_ask_user] HITLData → ExtendedHITLData 변환 훅
            for hitl in self.state.hitl_interrupts:
                if isinstance(hitl, ExtendedHITLData):
                    extended_interrupts.append(hitl)
                else:
                    extended_interrupts.append(
                        ExtendedHITLData(
                            mode=hitl.mode,  # type: ignore[arg-type]
                            tool_name=hitl.tool_name,
                            tool_call_id=hitl.tool_call_id,
                            payload=hitl.payload,
                            rejected=hitl.rejected,
                        )
                    )
            self.state.hitl_interrupts = extended_interrupts  # type: ignore[assignment]

    @observe(capture_input=False, capture_output=False)
    async def _resume_hitl(self) -> None:
        """HITL 인터럽트에서 사용자 응답으로 에이전트 실행을 재개합니다.

        세 가지 케이스를 처리합니다:
        1. rejected=True: 사용자가 도구 호출을 거부함 - 거부 메시지 주입
        2. mode="tool_call": _execute_tool_calls()로 도구를 재실행
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
                tool_messages.append(
                    ChatCompletionToolMessageParam(
                        role="tool",
                        content=f"User rejected the {hitl_data.tool_name} operation",
                        tool_call_id=hitl_data.tool_call_id,
                    )
                )
            elif hitl_data.mode == "tool_call":  # [ADDED in lec07_02_ask_user]
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
                tool_messages.append(
                    ChatCompletionToolMessageParam(
                        role="tool",
                        content=json.dumps(hitl_data.payload),
                        tool_call_id=hitl_data.tool_call_id,
                    )
                )

        # [ADDED in lec07_02_ask_user] tool_call 모드: _execute_tool_calls()로 도구 재실행
        if tool_calls:
            tool_results, nested_hitl_interrupts = await self._execute_tool_calls(tool_calls)
            if nested_hitl_interrupts:
                raise Exception(f"Nested HITL not supported: {nested_hitl_interrupts[0].tool_name}")
            tool_messages.extend(tool_results)

        self._extend_messages(list(tool_messages))
        self.state.hitl_interrupts = []
