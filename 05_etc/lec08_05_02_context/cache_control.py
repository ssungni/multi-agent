"""Extended from: lec08_04_cost/cache_control.py

이 버전은 4개의 cache_control 블록을 사용하여 축소 메시지(diminished message)도 캐싱합니다:
1. 첫 메시지 (시스템 프롬프트) - 거의 변경되지 않음
2. 마지막 메시지 - 최신 컨텍스트
3. 마지막 사용자 메시지 (요약 제외) - 사용자 입력 캐싱
4. 마지막 축소 메시지 (요약 또는 압축) - 컨텍스트 압축 결과 캐싱

축소 메시지란:
- SUMMARY_START_MARKER로 시작하는 user 메시지 (요약)
- COMPACTION_START_MARKER로 시작하는 tool 메시지 (압축된 도구 결과)

이를 통해 컨텍스트 크기를 줄이면서도 캐시 히트율을 유지합니다.
"""

from copy import deepcopy
from typing import Any

# [ADDED in lec08_05_context]
SUMMARY_START_MARKER = "[SYSTEM MESSAGE]"
COMPACTION_START_MARKER = "[Compacted]"


def apply_cache_control_blocks(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Claude의 캐싱 전략에 따라 메시지에 cache_control 블록을 적용합니다.

    캐시 제어 전략:
    Claude는 요청당 최대 4개의 cache_control 블록을 허용합니다.
    이 버전에서는 다음 위치에 배치합니다:
    1. 시스템 프롬프트 (첫 메시지) - 거의 변경되지 않음
    2. 마지막 메시지 - 최신 컨텍스트가 캐시되도록 보장
    3. 마지막 사용자 메시지 (요약 제외) - 사용자 입력 캐싱
    4. 마지막 축소 메시지 (요약/압축) - 컨텍스트 압축 결과 캐싱 [ADDED in lec08_05_context]

    축소 메시지란:
    - SUMMARY_START_MARKER("[SYSTEM MESSAGE]")로 시작하는 user 메시지
    - COMPACTION_START_MARKER("[Compacted]")로 시작하는 tool 메시지

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

    # [ADDED in lec08_05_context]
    # 마지막 사용자 메시지와 마지막 축소 메시지를 찾기 위한 플래그
    found_last_user_message = False
    found_last_diminished_message = False

    # 역순으로 순회하여 마지막 사용자 메시지와 마지막 축소 메시지 찾기
    for idx in range(len(messages) - 1, -1, -1):
        message = messages[idx]
        content = message.get("content")

        # 문자열이 아닌 콘텐츠는 건너뛰기 (예: 이미지, 구조화된 콘텐츠)
        if not isinstance(content, str):
            continue

        # [ADDED in lec08_05_context]
        # user 메시지 처리
        if message.get("role") == "user":
            # 축소 메시지인지 확인 (요약 메시지)
            if not found_last_diminished_message and content.startswith(SUMMARY_START_MARKER):
                found_last_diminished_message = True
                cache_control_indices.add(idx)
            # 일반 사용자 메시지
            elif not found_last_user_message and not content.startswith(SUMMARY_START_MARKER):
                found_last_user_message = True
                cache_control_indices.add(idx)

        # [ADDED in lec08_05_context]
        # tool 메시지 처리 (압축된 도구 결과)
        elif (
            not found_last_diminished_message
            and message.get("role") == "tool"
            and content.startswith(COMPACTION_START_MARKER)
        ):
            found_last_diminished_message = True
            cache_control_indices.add(idx)

        # [ADDED in lec08_05_context]
        # 둘 다 찾았으면 조기 종료
        if found_last_user_message and found_last_diminished_message:
            break

    # 선택된 메시지에 cache_control 블록 적용
    for idx in cache_control_indices:
        messages[idx]["cache_control"] = {"type": "ephemeral"}

    return messages
