"""HITL (Human-In-The-Loop) 데이터 구조.

이 모듈은 HITL 인터럽트를 나타내는 HITLData 모델을 정의합니다.
도구가 사용자 입력이 필요할 때 hitl_data가 설정된 ToolResult를 반환합니다.

lec06_02에서는 tool_result 모드만 지원합니다:
- 도구가 mode="tool_result"과 payload로 HITLData 반환
- 에이전트 일시정지, 사용자가 실제 결과 제공
- 에이전트가 사용자 제공 결과를 tool message로 주입하여 재개
"""

from typing import Any, Literal

from pydantic import BaseModel


class HITLData(BaseModel):
    """HITL 인터럽트 데이터 - 사용자 입력이 필요할 때 도구가 반환합니다.

    HITL 인터럽트는 도구가 에이전트 실행을 일시정지하고 사용자 입력을 요청할 수 있게 합니다.
    에이전트 루프는 이 인터럽트를 감지하고 중단하여 사용자 응답을 기다립니다.

    tool_result 모드: 사용자가 결과를 직접 제공
    - 도구가 mode="tool_result"과 payload=placeholder_result로 HITLData 반환
    - 에이전트 일시정지, 사용자가 실제 결과 제공
    - 에이전트가 사용자 제공 결과를 tool message로 주입하여 재개

    Attributes:
        mode: HITL 모드 - "tool_result"은 사용자가 결과를 직접 제공
        tool_name: 인터럽트를 트리거한 도구 이름
        tool_call_id: 도구 호출 ID (에이전트가 LLM 응답에서 채움)
        payload: 도구와 사용자 간 데이터를 주고받는 양방향 딕셔너리.
            (1) 도구가 사용자에게 보여줄 데이터(예: 초안 텍스트)를 담아 반환하고,
            (2) 사용자 입력 후 응답(예: 승인 여부, 피드백)으로 덮어써지며,
            (3) _resume_hitl()이 이 payload를 JSON으로 변환해 tool message로 주입합니다.
        rejected: 사용자가 도구 호출을 거부하면 True (에이전트가 거부 메시지 주입)
    """

    mode: Literal["tool_result"]
    tool_name: str
    tool_call_id: str = ""  # Agent fills this from the LLM response
    payload: dict[str, Any]
    rejected: bool = False
