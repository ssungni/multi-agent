"""컨텍스트 압축을 통한 메시지 히스토리 관리.

이 모듈은 도구 결과를 압축하여 컨텍스트 크기를 줄이는 기능을 제공합니다.
핵심 아이디어:
- 최근 5개의 도구 메시지는 보존 (모델이 참고할 수 있도록)
- 오래된 도구 메시지는 압축 (중요한 ID는 보존)
- 이미 압축된 메시지는 다시 압축하지 않음
"""

from __future__ import annotations

import json
from typing import Any, cast

from langfuse.decorators import observe
from litellm.types.completion import ChatCompletionMessageParam, ChatCompletionToolMessageParam

from lec08_05_02_context.tool import COMPACTION_START_MARKER, BaseTool


@observe(capture_input=False, capture_output=False)
def compact_context(
    messages: list[ChatCompletionMessageParam],
    tools: list[BaseTool] | None = None,
    keep_recent: int = 5,
) -> list[ChatCompletionMessageParam]:
    """도구 결과를 복원 가능한 방식으로 압축합니다.

    상세한 도구 결과를 다음을 포함하는 압축된 요약으로 교체합니다:
    - 결과 개수
    - 주요 ID (URL, corpus_id, file_id 등) - 필요시 재접근 가능
    - 전체 콘텐츠 검색 방법에 대한 가이던스

    각 도구의 compact_result 메서드를 사용하여 커스텀 압축 로직을 적용합니다.

    Args:
        messages: 입력 메시지 리스트
        tools: 커스텀 압축을 위한 BaseTool 인스턴스 리스트 (선택)
        keep_recent: 전체 보존할 최근 도구 메시지 개수 (기본값: 5)

    Returns:
        압축된 도구 결과를 포함한 메시지 리스트
    """
    tool_map = {tool.name: tool for tool in tools} if tools else {}

    # 어시스턴트 메시지에서 tool_call_id -> (tool_name, arguments) 맵 구축
    tool_info: dict[str, tuple[str, dict[str, Any]]] = {}
    for msg in messages:
        if msg.get("role") == "assistant":
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in cast(list[Any], tool_calls):
                    tc_id = cast(str, tc.get("id"))
                    tc_function = tc.get("function")
                    if tc_id and tc_function:
                        tool_name = cast(str, tc_function.get("name")) or ""
                        try:
                            arguments = json.loads(
                                cast(str, tc_function.get("arguments", "{}"))
                            )
                        except json.JSONDecodeError:
                            arguments = {}
                        tool_info[tc_id] = (tool_name, arguments)

    # 역순으로 순회하며, 최근 `keep_recent`개 도구 메시지는 건너뛰고 나머지 압축
    result: list[ChatCompletionMessageParam] = []
    skipped = 0

    for msg in reversed(messages):
        if msg.get("role") != "tool":
            result.append(msg)
            continue

        tool_call_id = cast(str, msg.get("tool_call_id", ""))
        if tool_call_id not in tool_info:
            # 도구 정보를 찾을 수 없으면 그대로 유지
            result.append(msg)
            continue

        tool_name, arguments = tool_info[tool_call_id]

        # 이미 압축된 메시지인지 확인
        content = str(msg.get("content", ""))
        if content.startswith(COMPACTION_START_MARKER):
            result.append(msg)
            continue

        # 최근 `keep_recent`개 도구 메시지는 보존
        if skipped < keep_recent:
            result.append(msg)
            skipped += 1
            continue

        # 이 도구 결과를 압축
        compacted_content = _compact_tool_content(tool_name, arguments, content, tool_map)
        result.append(
            ChatCompletionToolMessageParam(
                role="tool",
                content=compacted_content,
                tool_call_id=cast(str, tool_call_id),
            )
        )

    result.reverse()
    return result


def _compact_tool_content(
    tool_name: str,
    arguments: dict[str, Any],
    content: str,
    tool_map: dict[str, BaseTool] | None = None,
) -> str:
    """도구의 compact_result 메서드를 사용하여 도구 콘텐츠를 압축합니다.

    Args:
        tool_name: 도구 이름
        arguments: 도구 호출 인자
        content: 압축할 원본 콘텐츠
        tool_map: 도구 이름을 BaseTool 인스턴스로 매핑한 딕셔너리

    Returns:
        압축된 콘텐츠 문자열
    """
    # BaseTool의 compact_result 메서드 사용
    if tool_map and tool_name in tool_map:
        return tool_map[tool_name].compact_result(arguments, content)

    # tool_map에 없는 도구의 기본 압축 (정상 흐름에서는 발생하지 않음)
    return f"{COMPACTION_START_MARKER} {tool_name} result. Content omitted for space."
