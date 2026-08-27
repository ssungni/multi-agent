"""확장된 HITL 데이터 구조 및 ToolResult - tool_call 모드 지원.

lec06_02_hitl의 HITLData는 tool_result 모드만 지원합니다.
이 모듈은 tool_call 모드를 추가로 지원하는 ExtendedHITLData를 정의합니다.

또한 ExtendedHITLData를 hitl_data 필드에 저장할 수 있는
ExtendedToolResult를 제공합니다.

## tool_result 모드 vs tool_call 모드

tool_result 모드 (lec06_02_hitl 기존):
    - 도구가 placeholder 결과와 함께 HITLData(mode="tool_result") 반환
    - 에이전트 일시정지 → 사용자가 payload에 실제 결과를 채움
    - _resume_hitl()이 payload를 JSON으로 변환해 tool message로 직접 주입
    - 예시: ask_outline_approval — 사용자가 승인/거부 결과를 직접 제공
    - 도구는 재실행되지 않음

tool_call 모드 (lec07_02_ask_user 추가):
    - 도구가 질문과 함께 ExtendedHITLData(mode="tool_call") 반환
    - 에이전트 일시정지 → 사용자가 payload에 답변을 추가
    - _resume_hitl()이 _execute_tool_calls()로 도구를 재실행
    - 도구 재실행 결과를 tool message로 주입
    - 예시: ask_user_question — 사용자 답변을 받아 도구가 Q&A 콘텐츠를 생성

"""

from typing import Any, Literal

from pydantic import BaseModel


class ExtendedHITLData(BaseModel):
    """tool_call 모드를 지원하는 확장된 HITL 인터럽트 데이터.

    lec06_02_hitl.hitl.HITLData와 동일한 필드를 가지되,
    mode에 "tool_call"을 추가로 허용합니다.

    tool_call 모드:
    - 도구가 mode="tool_call"과 payload로 HITLData 반환
    - 에이전트 일시정지, 사용자가 payload에 응답 추가
    - _resume_hitl()이 assistant message의 arguments를 업데이트 (히스토리 정합성)
    - _execute_tool_calls()로 도구를 재실행, 결과를 tool message로 주입
    - 예시: ask_user_question — 사용자 답변을 받아 도구가 Q&A 콘텐츠를 생성

    Attributes:
        mode: HITL 모드 - "tool_result" 또는 "tool_call"
        tool_name: 인터럽트를 트리거한 도구 이름
        tool_call_id: 도구 호출 ID (에이전트가 LLM 응답에서 채움)
        payload: 도구와 사용자 간 데이터를 주고받는 양방향 딕셔너리
        rejected: 사용자가 도구 호출을 거부하면 True
    """

    mode: Literal["tool_result", "tool_call"]  # [ADDED in lec07_02_ask_user] "tool_call" 추가
    tool_name: str
    tool_call_id: str = ""
    payload: dict[str, Any]
    rejected: bool = False


class ExtendedToolResult(BaseModel):
    """ExtendedHITLData를 지원하는 확장된 도구 실행 결과.

    lec06_02_hitl.tool.ToolResult와 동일한 구조이지만,
    hitl_data 필드가 ExtendedHITLData를 허용합니다.

    Attributes:
        content: LLM에 도구 출력으로 반환될 문자열 결과
        artifact: 에이전트가 프로그래밍적으로 사용할 선택적 구조화 데이터
        hitl_data: 선택적 HITL 인터럽트 데이터 (ExtendedHITLData 지원)
    """

    content: str
    artifact: Any = None
    hitl_data: ExtendedHITLData | None = None
