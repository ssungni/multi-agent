"""Context 요약을 통한 메시지 히스토리 관리.

이 모듈은 오래된 대화를 요약하여 컨텍스트 크기를 줄이는 기능을 제공합니다.
Compaction으로 충분하지 않을 때 사용됩니다.

Strategy:
1. 최근 N개 메시지는 유지 (기본값: 6)
2. 나머지 오래된 메시지를 LLM을 사용하여 요약
3. 요약 시 도구 호출/응답 쌍이 분리되지 않도록 보장
4. corpus_id, URL 등의 식별자를 구조화된 형태로 보존
"""

import asyncio
import json
from typing import Any, Iterable, cast

from langfuse.decorators import langfuse_context, observe
from litellm import AllMessageValues
from litellm.types.completion import ChatCompletionContentPartParam, ChatCompletionMessageParam

from lec02_02_langfuse.router import router
from lec08_05_02_context.cache_control import COMPACTION_START_MARKER
from lec08_05_02_context.calculate_size import calculate_num_tokens

# Constants
MAX_SUMMARIZATION_TOKENS = 128000
MAX_SUMMARY_RESPONSE_TOKENS = 10000
MAX_SUMMARIZATION_RETRIES = 5
SUMMARIZATION_RETRY_DELAY_SECONDS = 0.5
SUMMARIZATION_MODEL = "gemini-3-flash"  # Cheap, fast model for summarization

# Summary message markers
SUMMARY_TAG_OPEN = "<summary>"


SUMMARIZATION_PROMPT = "\n".join(
    [
        "You are a context summarization assistant. Your task is to create a concise but complete summary of a conversation between an AI agent and tools.",
        "The summary will replace older messages, so you MUST preserve all identifiers needed to re-fetch information if needed later.",
        "",
        "Your summary MUST include:",
        "1. User's original query and intent",
        "2. Key findings and conclusions discovered so far",
        "3. Current progress and what remains to be done",
        "",
        "CRITICAL - Always preserve these URLs in a structured format:",
        "- Search queries that were used",
        "- URLs that were fetched",
        "",
        "Example format for referenced materials:",
        "```",
        "Searches performed: 'AI search', 'agentic loop'",
        "```",
        "",
        "Be concise but preserve ALL URLs. The agent can re-fetch full content using these URLs if needed.",
    ]
)


@observe(capture_input=False, capture_output=False)
async def summarize_context(
    working_messages: list[ChatCompletionMessageParam],
    original_messages: list[ChatCompletionMessageParam],
    keep_recent: int = 6,
    model: str = SUMMARIZATION_MODEL,
    max_tokens: int = MAX_SUMMARIZATION_TOKENS,
) -> list[ChatCompletionMessageParam]:
    """대화 컨텍스트를 요약하여 오래된 메시지를 압축합니다.

    Strategy:
    1. 최근 keep_recent개 메시지는 그대로 유지
    2. 나머지 오래된 메시지를 LLM으로 요약
    3. 도구 호출/응답 쌍이 분리되지 않도록 보장
    4. 요약 전에 compacted 도구 결과를 원본으로 복원 (토큰 제한 내에서)

    Args:
        working_messages: 현재 작업 중인 메시지 (compaction 등이 적용된 상태)
        original_messages: 원본 메시지 (append-only, 전체 내용 포함)
        keep_recent: 최근 N개 메시지를 유지 (기본값: 6)
        model: 요약에 사용할 모델 (기본값: Gemini Flash)
        max_tokens: 요약 입력의 최대 토큰 수 (기본값: 1,000,000)

    Returns:
        요약된 메시지 리스트 [시스템 메시지, 요약 메시지, ...최근 메시지들]
    """
    system_message = working_messages[0]
    chat_history = working_messages[1:]

    if len(chat_history) <= keep_recent:
        return working_messages

    # 도구 호출/응답 쌍을 보존하면서 메시지 분리
    messages_to_summarize, recent_messages = _split_messages_preserving_tool_pairs(
        chat_history, keep_recent
    )

    if not messages_to_summarize:
        return working_messages

    # Compacted 도구 결과를 원본으로 복원 (토큰 제한 내에서)
    messages_to_summarize = _restore_from_original_with_limit(
        messages_to_summarize, original_messages, max_tokens
    )

    # LLM을 사용하여 요약 생성 (재시도 로직 포함)
    summary = ""
    last_error: Exception | None = None

    for attempt in range(MAX_SUMMARIZATION_RETRIES):
        try:
            response = await router.acompletion(
                model=model,
                messages=cast(
                    list[AllMessageValues],
                    [
                        *messages_to_summarize,
                        {"role": "user", "content": SUMMARIZATION_PROMPT},
                    ],
                ),
                max_tokens=MAX_SUMMARY_RESPONSE_TOKENS,
                num_retries=0,
                metadata={
                    "purpose": "context_manager",
                    "source_name": "summarization",
                    "capture_cost": True,
                    "existing_trace_id": langfuse_context.get_current_trace_id(),
                    "parent_observation_id": langfuse_context.get_current_observation_id(),
                },
            )
            choice = response.choices[0]
            message = getattr(choice, "message", None)
            if message is not None:
                summary = message.content or ""
            if summary.strip():
                break
            raise ValueError("Empty summary returned from LLM")
        except Exception as e:
            last_error = e
            if attempt < MAX_SUMMARIZATION_RETRIES - 1:
                await asyncio.sleep(SUMMARIZATION_RETRY_DELAY_SECONDS * (attempt + 1))
            continue

    if not summary:
        error_msg = f"[Summarization Error: Failed to summarize context after {MAX_SUMMARIZATION_RETRIES} attempts"
        if last_error:
            error_msg += f" (last error: {type(last_error).__name__})"
        error_msg += "]"
        summary = error_msg

    # 요약 메시지 포맷 생성
    summary_message = "\n".join(
        [
            "[SYSTEM MESSAGE]",
            "The conversation context has become too long and older messages have been summarized below.",
            "You can reference information from the summary as needed.",
            "<summary>",
            summary,
            "</summary>",
            "[END OF SYSTEM MESSAGE]",
        ]
    )

    return [system_message, {"role": "user", "content": summary_message}, *recent_messages]


def _split_messages_preserving_tool_pairs(
    chat_history: list[ChatCompletionMessageParam],
    keep_recent: int,
) -> tuple[list[ChatCompletionMessageParam], list[ChatCompletionMessageParam]]:
    """도구 호출/응답 쌍을 보존하면서 메시지를 분리합니다.

    Strategy:
    최근 N개 메시지의 첫 메시지가 tool 응답이면, 해당 tool을 호출한 assistant까지
    포함하도록 역방향으로 확장합니다. 이를 통해 tool call/response 쌍이 분리되는 것을 방지합니다.

    Args:
        chat_history: 전체 대화 히스토리 (시스템 메시지 제외)
        keep_recent: 유지할 최근 메시지 수

    Returns:
        (요약할 메시지들, 유지할 최근 메시지들) 튜플
    """
    split_idx = len(chat_history) - keep_recent

    # 첫 메시지가 tool이면 역방향으로 확장하여 assistant 포함
    while split_idx > 0 and chat_history[split_idx].get("role") == "tool":
        tool_call_id = chat_history[split_idx].get("tool_call_id")
        if not tool_call_id:
            break

        # 이 tool call을 발행한 assistant 찾기
        found_assistant = False
        for i in range(split_idx - 1, -1, -1):
            msg = chat_history[i]
            if msg.get("role") == "assistant":
                tool_calls = msg.get("tool_calls")
                if tool_calls and isinstance(tool_calls, list):
                    assistant_tool_call_ids = {
                        str(tc.get("id"))
                        for tc in tool_calls
                        if isinstance(tc, dict) and tc.get("id")
                    }
                    if str(tool_call_id) in assistant_tool_call_ids:
                        # Assistant를 찾았으므로 split 위치를 여기로 이동
                        split_idx = i
                        found_assistant = True
                        break

        if not found_assistant:
            # Assistant를 못 찾으면 확장 중단
            break

    return chat_history[:split_idx], chat_history[split_idx:]


def _restore_from_original_with_limit(
    working_messages: list[ChatCompletionMessageParam],
    original_messages: list[ChatCompletionMessageParam],
    max_tokens: int,
) -> list[ChatCompletionMessageParam]:
    """Compacted 도구 결과를 원본에서 복원합니다 (토큰 제한 내에서).

    Strategy:
    1. 현재 working_messages의 토큰 수 계산
    2. 최신부터 역순으로 순회하면서
    3. Compacted된 tool 결과를 찾으면 원본으로 복원 시도
    4. 토큰 제한을 초과하지 않는 선에서만 복원

    이를 통해 요약 품질을 높이면서도 토큰 제한을 준수합니다.

    Args:
        working_messages: 작업 메시지 (compacted 상태일 수 있음)
        original_messages: 원본 메시지 (전체 내용 포함)
        max_tokens: 최대 토큰 수

    Returns:
        복원된 메시지 리스트
    """
    # tool_call_id -> 원본 tool 메시지 인덱스 생성
    original_tool_messages = {
        str(msg.get("tool_call_id")): msg
        for msg in original_messages
        if msg.get("role") == "tool" and msg.get("tool_call_id")
    }

    # 현재 토큰 수 계산
    current_tokens = sum(calculate_num_tokens(json.dumps(msg)) for msg in working_messages)

    # 최신부터 역순으로 순회하면서 compacted tool 복원
    for msg in reversed(working_messages):
        if msg.get("role") == "tool":
            content: str | Iterable[ChatCompletionContentPartParam] | None = msg.get("content", "")
            if content is None:
                continue

            tool_call_id = str(msg.get("tool_call_id", ""))

            # Compacted 메시지인지 확인
            if (
                isinstance(content, str)
                and content.startswith(COMPACTION_START_MARKER)
                and tool_call_id in original_tool_messages
            ):
                original_msg = original_tool_messages[tool_call_id]
                original_content: str | Iterable[ChatCompletionContentPartParam] | None = (
                    original_msg.get("content", "")
                )
                if original_content is None:
                    continue

                # 토큰 증가량 계산
                compacted_tokens = calculate_num_tokens(json.dumps(msg))
                original_tokens = calculate_num_tokens(json.dumps(original_msg))
                token_increase = original_tokens - compacted_tokens

                # 토큰 제한 내에서만 복원
                if current_tokens + token_increase <= max_tokens:
                    cast(dict[str, Any], msg)["content"] = original_content
                    current_tokens += token_increase
                else:
                    # 토큰 제한 초과 시 중단
                    break

    return working_messages
