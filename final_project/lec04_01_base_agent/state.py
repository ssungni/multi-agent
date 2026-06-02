"""에이전트 상태 관리 모듈.

에이전트의 대화 이력과 실행 상태를 추적하는 BaseAgentState 모델을 정의합니다.
"""

import warnings
from typing import TypeVar

warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

from litellm.types.completion import ChatCompletionMessageParam
from pydantic import BaseModel, SkipValidation
from typing_extensions import Annotated


class BaseAgentState(BaseModel):
    """모든 에이전트의 기본 상태 모델.

    에이전트 실행 루프에 필요한 핵심 상태를 추적합니다:
    - 사용할 LLM 모델
    - 대화 이력 (messages)
    - 현재 반복 횟수

    Attributes:
        model: LLM 모델 식별자 (예: "gpt-4", "claude-3-sonnet-20240229")
        messages: 대화 이력 (ChatCompletion 메시지 리스트)
        iteration_count: 에이전트 루프의 현재 반복 횟수 (0부터 시작)
    """

    model: str = "claude-4.5-sonnet"
    messages: Annotated[list[ChatCompletionMessageParam], SkipValidation] = []
    iteration_count: int = 0

    @property
    def working_messages(self) -> list[ChatCompletionMessageParam]:
        """컨텍스트 관리에 사용되는 메시지를 반환합니다.

        기본 구현에서는 모든 메시지를 그대로 반환합니다.
        이후 강의에서 컨텍스트 윈도우 관리(compaction, summarization 등)를 확장합니다.

        Returns:
            LLM에 전송할 메시지 리스트
        """
        return self.messages


# 에이전트 상태를 위한 제네릭 타입 변수
# 서브클래스에서 자체 상태 타입을 정의하면서도 타입 안전성을 유지할 수 있습니다.
TState = TypeVar("TState", bound=BaseAgentState)
