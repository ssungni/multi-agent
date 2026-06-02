"""Lecture 08-05-02 최종 통합 실행 예제 - Context Engineering.

이 모듈은 기존 OptimizedOrchestratorAgent를 상속하여 Context Engineering을 적용하는 방법을 시연합니다.
_hook_pre_llm_call()을 오버라이드하여 컨텍스트 압축과 캐시 제어를 추가합니다.

통합된 기능 목록:
    1. Lecture 02: LiteLLM Router + Langfuse
       - router를 통한 LLM 호출 추상화
       - setup_langfuse()를 통한 observability 설정

    2. Lecture 04~06: OrchestratorAgent 전체 파이프라인
       - Outliner → Researcher → Writer → Final Report
       - Sub-agent 조율 및 상태 관리

    3. Lecture 08-04: Cost Optimization
       - ModelSelector를 통한 작업별 모델 선택
       - Cache Control (3-block strategy)

    4. Lecture 08-05-02: Context Engineering
       - ContextManager를 통한 2단계 압축 전략
       - Compaction: 도구 결과 압축으로 토큰 절감
       - Summarization: 오래된 대화 요약으로 컨텍스트 크기 관리
       - 4번째 cache_control 블록 적용 (축소 메시지)

학습 포인트:
    이 예제를 통해 다음을 학습합니다:
    1. 기존 에이전트를 상속하여 Context Engineering을 추가하는 패턴
       - OptimizedOrchestratorAgent를 상속하고 setup()과 _hook_pre_llm_call()만 오버라이드
       - 기존 에이전트의 도구, 상태 관리, 워크플로우를 그대로 활용
    2. ContextManager를 통한 2단계 압축 전략 적용
    3. Cache Control과 Context Engineering의 결합
    4. 각 컴포넌트가 어떻게 협력하여 완전한 시스템을 만드는지 이해

실행 방법:
    rye run lec08-05-02

통합 아키텍처:
    ContextManagedOrchestratorAgent (this file)
        ├── extends OptimizedOrchestratorAgent (lec08_04_cost/main.py)
        │     ├── ModelSelector (작업별 모델 선택)
        │     ├── Cache Control (3-block strategy)
        │     └── Outliner → Researcher → Writer 파이프라인
        │
        ├── overrides setup()
        │     └── ContextManager 초기화
        │
        ├── overrides _hook_pre_llm_call()
        │     ├── ContextManager.process() (Compaction + Summarization)
        │     └── apply_cache_control_blocks() (4개 블록)
        │
        └── tracked by Langfuse (lec02_02_langfuse/observability.py)
              └── via LiteLLM Router (lec02_01_litellm/router.py)

참고:
    - OptimizedOrchestratorAgent: lecture/lec08_04_cost/main.py
    - ContextManager: lecture/lec08_05_02_context/manager.py
    - Cache Control: lecture/lec08_05_02_context/cache_control.py
"""

import asyncio
import copy
import os
import sys
from typing import Any, cast

from litellm.types.completion import ChatCompletionMessageParam
from typing_extensions import Self

from lec02_02_langfuse.observability import setup_langfuse
from lec06_01_orchestrator.main import print_report
from lec08_04_cost.main import OptimizedOrchestratorAgent
from lec08_05_02_context.cache_control import apply_cache_control_blocks
from lec08_05_02_context.manager import ContextManager


class ContextManagedOrchestratorAgent(OptimizedOrchestratorAgent):
    """Context Engineering이 적용된 OptimizedOrchestratorAgent.

    기존 OptimizedOrchestratorAgent를 상속하고:
    1. setup()에서 ContextManager 초기화
    2. _hook_pre_llm_call()에서 컨텍스트 압축 + 캐시 제어 적용

    이 에이전트는 OptimizedOrchestratorAgent의 모든 기능을 그대로 사용하면서:
    - ContextManager를 통한 2단계 압축 (Compaction + Summarization)
    - apply_cache_control_blocks를 통한 4개 캐시 블록 적용

    오버라이드 메서드:
        setup(): ContextManager 초기화 추가
        _hook_pre_llm_call(): 컨텍스트 압축 + 캐시 제어 적용
    """

    context_manager: ContextManager | None = None

    @classmethod
    async def setup(  # type: ignore[override]
        cls,
        user_request: str,
        max_iterations: int = 20,
    ) -> Self:
        """새 ContextManagedOrchestratorAgent 인스턴스를 생성합니다.

        OptimizedOrchestratorAgent.setup()을 호출한 후 ContextManager를 추가로 초기화합니다.

        Args:
            user_request: 사용자의 리포트 요청
            max_iterations: 최대 반복 횟수 (기본값: 20)

        Returns:
            Self: 초기화된 ContextManagedOrchestratorAgent 인스턴스
        """
        self = await super().setup(
            user_request=user_request,
            max_iterations=max_iterations,
        )

        # Context Engineering: ContextManager 초기화
        self.context_manager = ContextManager(
            compaction_threshold=128000,
            compaction_keep_recent=5,
            compaction_tools=None,
            summarization_threshold=100000,
            summarization_keep_recent=6,
        )

        return self

    async def _hook_pre_llm_call(self) -> list[ChatCompletionMessageParam]:
        """LLM 호출 전에 컨텍스트 압축 + Cache Control 블록을 적용합니다.

        1. 메시지를 deep copy
        2. ContextManager로 컨텍스트 압축 (Compaction + Summarization)
        3. apply_cache_control_blocks로 캐시 제어 블록 적용 (4개 블록)

        Returns:
            컨텍스트 압축 + cache_control 블록이 적용된 메시지 리스트
        """
        messages = copy.deepcopy(self.state.messages)

        # Context Engineering: 2단계 압축 전략 적용
        if self.context_manager:
            messages = await self.context_manager.process(
                working_messages=messages,
                original_messages=self.state.messages,
            )

        # Cache Control: 4개 블록 적용 (축소 메시지 포함)
        return cast(
            list[ChatCompletionMessageParam],
            apply_cache_control_blocks(cast(list[dict[str, Any]], messages)),
        )


def print_cache_control_info(messages: list[dict[str, Any]]) -> None:
    """cache_control 적용 정보를 출력합니다.

    Args:
        messages: cache_control이 적용된 메시지 리스트
    """
    print("\nCache Control Blocks Applied:")
    for i, msg in enumerate(messages):
        if msg.get("cache_control"):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if isinstance(content, str):
                content_preview = content[:50] + "..." if len(content) > 50 else content
            else:
                content_preview = "[structured content]"
            print(f"  [{i}] {role}: {content_preview}")


async def main() -> None:
    """통합 실행 예제 메인 함수.

    OptimizedOrchestratorAgent를 상속하여 Context Engineering을 적용한 데모입니다.
    Outliner → Researcher → Writer 전체 파이프라인을 실행하면서
    ContextManager와 Cache Control이 어떻게 적용되는지 보여줍니다.
    """
    setup_langfuse()

    print("=" * 70)
    print("Context Engineering Demo - OptimizedOrchestratorAgent with Context Management")
    print("=" * 70)

    # SERPER_API_KEY 확인
    if not os.environ.get("SERPER_API_KEY"):
        print("\n오류: SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Serper API 키는 https://serper.dev 에서 발급받을 수 있습니다.")
        print("\n사용법:")
        print("  export SERPER_API_KEY='your-api-key'")
        print("  rye run lec08-05-02")
        sys.exit(1)

    user_request = "현재 AI 트렌드에 대한 리포트를 작성해주세요."

    agent = await ContextManagedOrchestratorAgent.setup(
        user_request=user_request,
        max_iterations=20,
    )

    print(f"\n요청: {user_request}")
    print(f"Model: {agent.model}")
    print(f"Tools: {[tool.name for tool in agent.tools]}")
    if agent.context_manager:
        print(
            f"Context Manager: enabled (compaction={agent.context_manager.compaction_threshold}, "
            f"summarization={agent.context_manager.summarization_threshold})"
        )
    else:
        print("Context Manager: disabled")
    print("=" * 70 + "\n")

    print("Running agent...\n")

    try:
        await agent.run()
    except Exception as e:
        print(f"\n오류 발생: {e}")
        sys.exit(1)

    # 최종 리포트 출력
    print_report(agent)

    # cache_control 적용 정보 (마지막 호출 기준)
    cached_messages = apply_cache_control_blocks(
        cast(list[dict[str, Any]], agent.state.messages)
    )
    print_cache_control_info(cached_messages)

    print(f"\n완료! (iterations: {agent.state.iteration_count})")
    print(f"현재 Phase: {agent.state.current_phase}")

    print("\n학습 요약:")
    print("  1. OptimizedOrchestratorAgent를 상속하여 Context Engineering 추가")
    print("  2. ContextManager를 통한 자동 컨텍스트 압축 (Compaction + Summarization)")
    print("  3. Cache Control 4개 블록을 통한 비용 최적화 (축소 메시지 포함)")
    print("  4. 전체 Report Generation 파이프라인에서 Context Engineering 적용")


if __name__ == "__main__":
    asyncio.run(main())
