"""Claude API 캐시 최적화를 위한 cache_control 블록 관리 유틸리티.

Claude API의 캐시 동작을 최적화하기 위해 메시지에 cache_control 블록을 적용합니다.

Claude 문서에 따르면:
- 최대 4개의 cache_control 블록 허용
- 캐시 쓰기: 기본 입력 토큰 가격의 1.25배
- 캐시 읽기: 기본 입력 토큰 가격의 0.1배 (90% 절감!)
- 시스템은 첫 번째 캐시 블록 + 최신 3개 캐시 블록을 유지해야 함

참고: https://docs.claude.com/en/docs/build-with-claude/prompt-caching

Note:
    이 버전은 기본적인 cache_control 적용만 수행합니다.
    lec08_05_context에서 compaction/summarization이 구현되면,
    축소 메시지(요약, 압축된 도구 출력)에 대한 cache_control 적용이 추가됩니다.
"""

from copy import deepcopy
from typing import Any


def apply_cache_control_blocks(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Claude의 캐싱 전략에 따라 메시지에 cache_control 블록을 적용합니다.

    캐시 제어 전략:
    Claude는 요청당 최대 4개의 cache_control 블록을 허용합니다.
    이 버전에서는 다음 위치에 배치합니다:
    1. 시스템 프롬프트 (첫 메시지) - 거의 변경되지 않음
    2. 마지막 메시지 - 최신 컨텍스트가 캐시되도록 보장
    3. 마지막 사용자 메시지 - 사용자 입력 캐싱
    Note:
        lec08_05_context에서 compaction/summarization이 구현되면,
        4번째 블록으로 마지막 축소 메시지(요약/압축)에 대한 캐싱이 추가됩니다.

    캐싱 이점:
    - 캐시 쓰기: 기본 입력 토큰 가격의 1.25배 (일회성 비용)
    - 캐시 읽기: 기본 입력 토큰 가격의 0.1배 (90% 절감!)
    - 반복되는 컨텍스트에 효과적 (시스템 프롬프트, 대화 이력)

    Args:
        messages: 처리할 채팅 완성 메시지 리스트 (deep copy됨)

    Returns:
        cache_control 블록이 적절히 적용된 새 메시지 리스트
    """
    # 원본 메시지 수정을 피하기 위해 deep copy
    messages = deepcopy(messages)
    if not messages:
        return messages

    # 기존 cache_control 블록 제거
    for msg in messages:
        if msg.get("cache_control"):
            msg.pop("cache_control", None)

    # 첫 메시지와 마지막 메시지는 항상 캐시
    cache_control_indices = {0, len(messages) - 1}

    # 마지막 사용자 메시지 찾기
    for idx in range(len(messages) - 1, -1, -1):
        message = messages[idx]
        content = message.get("content")

        # 문자열이 아닌 콘텐츠는 건너뛰기 (예: 이미지, 구조화된 콘텐츠)
        if not isinstance(content, str):
            continue

        # 사용자 메시지 발견
        if message.get("role") == "user":
            cache_control_indices.add(idx)
            break

    # 선택된 메시지에 cache_control 블록 적용
    for idx in cache_control_indices:
        messages[idx]["cache_control"] = {"type": "ephemeral"}

    return messages
