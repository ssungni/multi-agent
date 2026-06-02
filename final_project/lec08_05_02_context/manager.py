"""Context 관리를 통한 2단계 압축 전략.

이 모듈은 Compaction과 Summarization을 통합하여 컨텍스트 크기를 관리합니다.

Strategy:
1. Context 크기가 compaction_threshold(128K)를 초과하면 compaction 실행
2. Compaction 후에도 summarization_threshold(100K)를 초과하면 summarization 실행

이를 통해 단계적으로 컨텍스트를 압축하여 토큰 사용을 최적화합니다.
"""

from langfuse.decorators import observe
from litellm.types.completion import ChatCompletionMessageParam

from lec08_05_02_context.calculate_size import calculate_context_size
from lec08_05_02_context.compaction import compact_context
from lec08_05_02_context.summarization import summarize_context
from lec08_05_02_context.tool import BaseTool

COMPACTION_THRESHOLD = 128000
SUMMARIZATION_THRESHOLD = 100000


class ContextManager:
    """2단계 압축 전략을 사용하는 컨텍스트 관리자.

    Attributes:
        compaction_threshold: Compaction을 시작하는 토큰 임계값
        summarization_threshold: Summarization을 시작하는 토큰 임계값
        compaction_keep_recent: Compaction 시 유지할 최근 도구 메시지 개수
        summarization_keep_recent: Summarization 시 유지할 최근 메시지 개수
    """

    def __init__(
        self,
        compaction_threshold: int = COMPACTION_THRESHOLD,
        compaction_keep_recent: int = 5,
        compaction_tools: list[BaseTool] | None = None,
        summarization_threshold: int = SUMMARIZATION_THRESHOLD,
        summarization_keep_recent: int = 6,
    ):
        self.compaction_threshold = compaction_threshold
        self.compaction_keep_recent = compaction_keep_recent
        self.compaction_tools = compaction_tools
        self.summarization_threshold = summarization_threshold
        self.summarization_keep_recent = summarization_keep_recent

    @observe(capture_input=False, capture_output=False)
    async def process(
        self,
        working_messages: list[ChatCompletionMessageParam],
        original_messages: list[ChatCompletionMessageParam],
    ) -> list[ChatCompletionMessageParam]:
        """2단계 압축 전략으로 컨텍스트를 처리합니다.

        Stage 1: Compaction
        - context_size > compaction_threshold이면 도구 결과를 압축

        Stage 2: Summarization
        - compacted_size > summarization_threshold이면 오래된 대화를 요약

        Args:
            working_messages: 현재 작업 중인 메시지 (compaction 등이 적용된 상태)
            original_messages: 원본 메시지 (append-only, 전체 내용 포함)

        Returns:
            처리된 메시지 리스트 (압축 및 요약 적용)
        """
        context_size = calculate_context_size(working_messages)
        if context_size < self.compaction_threshold:
            return working_messages

        compacted_messages = compact_context(
            messages=working_messages,
            tools=self.compaction_tools,
            keep_recent=self.compaction_keep_recent,
        )

        if calculate_context_size(compacted_messages) >= self.summarization_threshold:
            return await summarize_context(
                working_messages=compacted_messages,
                original_messages=original_messages,
                keep_recent=self.summarization_keep_recent,
            )

        return compacted_messages
