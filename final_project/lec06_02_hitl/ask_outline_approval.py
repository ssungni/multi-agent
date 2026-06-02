"""AskOutlineApproval Tool - 아웃라인 승인을 위한 HITL 도구.

이 도구는 lec06_02_hitl의 HITL Base 메커니즘을 활용하여 Outliner Agent가 생성한
아웃라인을 사용자에게 보여주고 승인을 요청합니다:
- 사용자 응답이 없으면: hitl_data가 포함된 ToolResult를 반환하여 에이전트 실행 일시정지
- 사용자가 승인하면: "approved" 상태로 ToolResult 반환하여 실행 재개
- 사용자가 수정 요청하면: 수정 피드백과 함께 ToolResult 반환하여 Outliner Agent 재실행

오케스트레이터는 이 도구를 사용하여 Outliner Agent가 생성한 아웃라인에 대한
사용자 승인을 받고, 수정 요청 시 피드백을 반영하여 아웃라인을 재생성할 수 있습니다.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

from lec06_02_hitl.hitl import HITLData
from lec06_02_hitl.state import BaseAgentState
from lec06_02_hitl.tool import BaseTool, ToolResult


class AskOutlineApprovalPayload(BaseModel):
    """AskOutlineApprovalTool의 페이로드 데이터.

    Attributes:
        outline_text: 사용자에게 보여줄 아웃라인 텍스트
        approved: 사용자가 아웃라인을 승인했는지 여부 (None이면 HITL 인터럽트)
        revision_feedback: 사용자가 제공한 수정 요청 피드백 (approved=False일 때만 사용)
    """

    outline_text: str
    approved: bool | None = None
    revision_feedback: str = ""

    @field_validator("revision_feedback")
    @classmethod
    def validate_revision_feedback(cls, v: str, info) -> str:
        """수정 피드백이 approved=False일 때 제공되었는지 검증합니다."""
        approved = info.data.get("approved")
        if approved is False and not v:
            raise ValueError("Revision feedback is required when outline is not approved")
        return v

    def to_content(self) -> str:
        """승인 결과를 문자열로 변환합니다."""
        if self.approved:
            return f"Outline approved by user.\n\nOutline:\n{self.outline_text}"
        return (
            f"Outline revision requested by user.\n\n"
            f"Outline:\n{self.outline_text}\n\n"
            f"Revision feedback: {self.revision_feedback}"
        )


class AskOutlineApprovalTool(BaseTool[BaseAgentState]):
    """생성된 아웃라인에 대한 사용자 승인을 요청하는 도구.

    이 도구는 HITL 메커니즘을 활용하여 에이전트가 실행을 일시정지하고
    사용자로부터 아웃라인 승인 또는 수정 요청을 받을 수 있게 합니다.

    사용 케이스:
    1. Outliner Agent가 생성한 아웃라인을 사용자에게 보여줌
    2. 사용자가 아웃라인을 승인하면 다음 단계(Researcher Agent)로 진행
    3. 사용자가 수정을 요청하면 피드백을 받아 Outliner Agent 재실행
    4. 오케스트레이터가 사용자 결정에 따라 워크플로우 제어

    HITL 모드: tool_result (사용자가 승인/수정 결과를 제공)
    """

    name = "ask_outline_approval"
    description = (
        "Use this tool to show the generated outline to the user and ask for approval. "
        "The user can either approve the outline to proceed to the next step (research), "
        "or request revisions with specific feedback. "
        "This enables the orchestrator to gather user approval before continuing the workflow."
    )
    parameters = {
        "type": "object",
        "properties": {
            "outline_text": {
                "type": "string",
                "description": "The formatted outline text to show to the user. Should be a clear, readable representation of the outline including title, sections, and subsections.",
            },
        },
        "required": ["outline_text"],
        "additionalProperties": False,
    }

    async def _execute(
        self,
        state: BaseAgentState,  # noqa: ARG002
        **kwargs: Any,
    ) -> ToolResult:
        """사용자에게 아웃라인 승인을 요청합니다.

        Args:
            state: 현재 에이전트 상태 (사용되지 않음)
            **kwargs: 도구 인자
                - outline_text: 사용자에게 보여줄 아웃라인 텍스트
                - tool_call_id: 도구 호출 ID

        Returns:
            ToolResult
        """
        outline_text: str = kwargs.get("outline_text", "")

        # approved가 None이면 유효성 검증을 건너뜀 (HITL 인터럽트 케이스)
        payload_data: dict[str, str | bool | None] = {
            "outline_text": outline_text,
            "approved": None,
            "revision_feedback": "",
        }

        try:
            data = AskOutlineApprovalPayload.model_validate(payload_data)
        except Exception as e:
            return ToolResult(artifact=None, content=f"Error: {e}")

        return ToolResult(
            content="Waiting for user to approve or request revision for the outline",
            artifact=None,
            hitl_data=HITLData(
                mode="tool_result",
                tool_name="ask_outline_approval",
                payload=data.model_dump(),
            ),
        )


# 도구 인스턴스 생성 및 export
ask_outline_approval_tool = AskOutlineApprovalTool()
