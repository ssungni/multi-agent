"""AskUser Tool - HITL 인터랙션을 통한 사용자 질문 도구.

이 도구는 lec06_02_hitl에서 구현한 HITL Base 메커니즘을 활용합니다:
- 답변이 없으면: hitl_data가 포함된 ToolResult 반환하여 에이전트 실행 일시정지
- 답변이 제공되면: 포맷된 Q&A 콘텐츠로 ToolResult 반환하여 실행 재개

에이전트는 실행 중 사용자에게 질문하여 선호도, 요구사항, 구현 선택에 대한
의사결정을 수집할 수 있습니다.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

from lec06_02_hitl.tool import BaseTool, ToolResult
from lec07_02_ask_user.hitl import ExtendedHITLData
from lec07_02_ask_user.state import ExtendedAgentState


class AskUserQuestionOption(BaseModel):
    """사용자 질문의 선택지 옵션.

    Attributes:
        label: 선택지의 표시 텍스트 (1-5 단어, 간결하게)
        description: 이 선택지가 의미하는 바 또는 선택 시 결과에 대한 설명
    """

    label: str
    description: str


class AskUserQuestion(BaseModel):
    """사용자에게 할 질문 구조.

    Attributes:
        question: 사용자에게 할 완전한 질문 문장
        header: 칩/태그로 표시될 짧은 라벨 (최대 12자)
        multiSelect: 여러 옵션 선택 가능 여부
        options: 질문의 선택지 리스트 (2-4개)
    """

    question: str
    header: str
    multiSelect: bool
    options: list[AskUserQuestionOption]


class AskUserQuestionPayload(BaseModel):
    """AskUserQuestionTool의 페이로드 데이터.

    Attributes:
        questions: 사용자에게 할 질문 리스트
        answers: 사용자가 제공한 답변 리스트 (비어있으면 HITL 인터럽트)
    """

    questions: list[AskUserQuestion] = []
    answers: list[str] = []

    @field_validator("answers")
    @classmethod
    def validate_answers_length(cls, v: list[str], info) -> list[str]:
        """답변 리스트가 비어있거나 질문 개수와 일치하는지 검증합니다."""
        if not v:
            return v

        questions = info.data.get("questions", [])
        if len(v) != len(questions):
            raise ValueError(
                f"Answers length ({len(v)}) must match questions length ({len(questions)}) or be empty"
            )
        return v

    def to_content(self) -> str:
        """각 질문과 답변을 매핑한 문자열 표현을 생성합니다."""
        lines = []
        for question, answer in zip(self.questions, self.answers):
            lines.append(f"{question.question}\nAnswer: {answer}")
        return "\n\n".join(lines)


class AskUserQuestionTool(BaseTool[ExtendedAgentState]):  # type: ignore[type-var]
    """실행 중 사용자에게 질문하는 도구.

    이 도구는 HITL 메커니즘을 활용하여 에이전트가 실행을 일시정지하고
    사용자로부터 입력을 받을 수 있게 합니다.

    사용 케이스:
    1. 사용자 선호도나 요구사항 수집
    2. 모호한 지시사항 명확화
    3. 작업 중 구현 선택에 대한 의사결정 획득
    4. 어떤 방향으로 진행할지 사용자에게 선택지 제공

    사용자는 항상 'Other'를 선택하여 커스텀 텍스트 입력을 제공할 수 있습니다.
    """

    name = "ask_user_question"
    description = (
        "Use this tool when you need to ask the user questions during execution. This allows you to: "
        "1. Gather user preferences or requirements, 2. Clarify ambiguous instructions, "
        "3. Get decisions on implementation choices as you work, 4. Offer choices to the user about what direction to take. "
        "Users will always be able to select 'Other' to provide custom text input."
    )
    parameters = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "description": "Questions to ask the user (1-4 questions)",
                "minItems": 1,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The complete question to ask the user. Should be clear, specific, and end with a question mark. If multiSelect is true, phrase it accordingly.",
                        },
                        "header": {
                            "type": "string",
                            "description": "Very short label displayed as a chip/tag (max 12 chars). Examples: 'Auth method', 'Library', 'Approach'.",
                        },
                        "multiSelect": {
                            "type": "boolean",
                            "description": "Set to true to allow the user to select multiple options instead of just one. Use when choices are not mutually exclusive.",
                        },
                        "options": {
                            "type": "array",
                            "description": "The available choices for this question. Must have 2-4 options. Each option should be a distinct choice. There should be no 'Other' option, that will be provided automatically.",
                            "minItems": 2,
                            "maxItems": 4,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                        "description": "The display text for this option (1-5 words, concise).",
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Explanation of what this option means or what will happen if chosen.",
                                    },
                                },
                                "required": ["label", "description"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["question", "header", "multiSelect", "options"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["questions"],
        "additionalProperties": False,
    }

    async def _execute(
        self,
        state: ExtendedAgentState,  # noqa: ARG002
        **kwargs: Any,
    ) -> ToolResult:
        """사용자에게 질문을 합니다.

        Args:
            state: 현재 에이전트 상태 (사용되지 않음)
            **kwargs: 도구 인자
                - questions: 사용자에게 할 질문 리스트
                - answers: 사용자가 제공한 답변 리스트 (없으면 HITL 인터럽트)
                - tool_call_id: 도구 호출 ID

        Returns:
            ToolResult:
                - answers가 없으면: hitl_data가 포함되어 에이전트 일시정지
                - answers가 있으면: 포맷된 Q&A 콘텐츠로 에이전트 재개
        """
        questions: list[dict[str, Any]] = kwargs.get("questions", [])
        answers: list[str] | None = kwargs.get("answers")
        if answers is None:
            answers = []

        try:
            data = AskUserQuestionPayload.model_validate(
                {"questions": questions, "answers": answers}
            )
        except Exception as e:
            return ToolResult(artifact=None, content=f"Error: {e}")

        if not data.answers:
            # ToolResult.hitl_data는 HITLData 타입이므로 ExtendedHITLData를
            # 저장하려면 model_construct로 Pydantic 검증을 우회합니다.
            return ToolResult.model_construct(
                content="Need to ask user questions",
                artifact=None,
                hitl_data=ExtendedHITLData(  # type: ignore[arg-type]
                    mode="tool_call",
                    tool_name="ask_user_question",
                    payload=data.model_dump(),
                ),
            )

        return ToolResult(artifact=data.answers, content=data.to_content())


# 도구 인스턴스 생성 및 export
ask_user_question_tool = AskUserQuestionTool()
