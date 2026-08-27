"""Lecture 08-04 통합 실행 예제 - Cache Control + 모델 전환 + Loop 최적화 + 검색 최적화.

이 모듈은 다섯 가지 비용 최적화 전략을 결합한 통합 데모를 제공합니다:
1. Cache Control: Claude API의 cache_control로 반복 컨텍스트 비용 90% 절감
2. 모델 전환 (Model Selection): Evaluator에 경량 모델(haiku) 사용
3. Adaptive max_iterations: 섹션 수 기반 동적 반복 제한
4. SearchAgent 파라미터 제한: max_iterations=5, 쿼리 3개, 결과 20개로 제한
5. 검색 결과 선별 전달: LLM 기반 관련성 필터링으로 불필요한 토큰 전달 방지

데모 흐름:
    Optimized - 작업별 모델 전환 + Loop 최적화 + Cache Control

학습 포인트:
    1. 기존 에이전트 상속을 통한 Evaluator 모델 경량화
       - OutlinerAgent → OptimizedOutlinerAgent: evaluator를 haiku로 변경
       - ResearcherAgent → OptimizedResearcherWorkflow: evaluator를 haiku로 변경
       - WriterAgent → OptimizedWriterAgent: evaluator를 haiku로 변경

    2. Constructor Injection을 통한 Optimized Sub-agent 교체
       - OrchestratorAgent.setup()에서 tools 리스트를 오버라이드
       - CallOutlinerTool(subagent_class=OptimizedOutlinerAgent) 형태로 주입

    3. Adaptive max_iterations: 섹션 수 기반 동적 반복 제한

    4. 토큰 기반 비용 추정
       - 모델별 pricing table 내장
       - Langfuse 트레이스와 연동 가능

    5. Claude Cache Control
       - 최대 4개의 cache_control 블록 허용 (이 강의에서는 3개 사용)
       - 캐시 읽기: 기본 입력 토큰 가격의 0.1배 (90% 절감!)
       - 적용 위치: 시스템 프롬프트, 마지막 메시지, 마지막 사용자 메시지

실행 방법:
    rye run lec08-04

참고:
    - OrchestratorAgent: lecture/lec06_01_orchestrator/agent.py
    - Cache Control: lecture/lec08_04_cost/cache_control.py
    - ModelSelector: lecture/lec08_04_cost/model_selector.py
"""

import asyncio
import copy
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, cast

from langfuse.decorators import observe
from litellm.types.completion import ChatCompletionMessageParam
from typing_extensions import Self

from lec02_02_langfuse.observability import setup_langfuse
from lec04_02_tools.schemas import ReferenceDocument
from lec05_01_outliner.agent import OutlinerAgent
from lec05_01_outliner.tools import GenerateOutlineTool
from lec05_02_researcher.agent import ResearcherWorkflow
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer.agent import WriterAgent
from lec05_03_writer.tools import PolishReportTool, WriteSectionTool
from lec06_01_orchestrator.agent import OrchestratorAgent
from lec06_01_orchestrator.main import print_report
from lec06_01_orchestrator.tools import (
    CallOutlinerTool,
    CallResearcherTool,
    CallWriterTool,
    FinalAnswerTool,
)
from lec08_04_cost.cache_control import apply_cache_control_blocks
from lec08_04_cost.evaluators import (
    ScoredOutlineEvaluator,
    ScoredReportEvaluator,
    ScoredRequiredInfoEvaluator,
    ScoredSectionEvaluator,
)
from lec08_04_cost.model_selector import ModelSelector, TaskType
from lec08_04_cost.search import FilteringSearchTool, OptimizedSearchAgent

# =============================================================================
# 실행 결과 데이터 클래스
# =============================================================================


@dataclass
class RunResult:
    """에이전트 실행 결과를 저장하는 데이터 클래스."""

    label: str
    elapsed_time: float = 0.0
    iteration_count: int = 0
    agent_type: str = ""
    optimizations: list[str] = field(default_factory=list)
    has_report: bool = False
    report_title: str = ""
    report_sections: int = 0


# =============================================================================
# 비용 추정 유틸리티
# =============================================================================

# 모델별 가격 테이블 (USD per 1M tokens)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-4.5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-4.5-haiku": {"input": 1.0, "output": 5.0},
    "claude-4-sonnet": {"input": 3.0, "output": 15.0},
    "gemini-3-flash": {"input": 0.5, "output": 1.0},
    "gpt-4.1-mini": {"input": 0.4, "output": 1.6},
}


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """토큰 사용량 기반으로 비용을 추정합니다.

    Args:
        model: 모델 이름
        input_tokens: 입력 토큰 수
        output_tokens: 출력 토큰 수

    Returns:
        추정 비용 (USD)
    """
    pricing = MODEL_PRICING.get(model, {"input": 3.0, "output": 15.0})
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


# =============================================================================
# Optimized Sub-agents (ModelSelector를 통한 모델 경량화)
# =============================================================================


class OptimizedOutlinerAgent(OutlinerAgent):
    """ModelSelector가 적용된 OutlinerAgent.

    최적화 내용:
    - ModelSelector로 Generation/Evaluation 모델을 자동 선택
    - ScoredOutlineEvaluator가 score >= threshold로 passed를 도출 (soft pass 내장)
    - Tool 내부 평가 루프가 score 기반 passed를 자동 활용하므로 에이전트 레벨 재평가 불필요
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        topic: str,
        clarified_requirements: str = "",
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 10,
    ) -> Self:
        selector = ModelSelector()
        _ = model  # ModelSelector가 모델을 자동 선택하므로 무시

        self = await super().setup(
            topic=topic,
            clarified_requirements=clarified_requirements,
            model=selector.select(TaskType.GENERATION).model,
            max_iterations=max_iterations,
        )
        # SearchTool → FilteringSearchTool로 교체 (쿼리 3개, 결과 20개 제한)
        self.tools = [FilteringSearchTool() if t.name == "search_web" else t for t in self.tools]
        # GenerateOutlineTool 내부 evaluator를 ScoredOutlineEvaluator로 교체
        eval_model = selector.select(TaskType.EVALUATION).model
        for tool in self.tools:
            if isinstance(tool, GenerateOutlineTool):
                tool.evaluator = ScoredOutlineEvaluator(model=eval_model)
        return self

    async def _hook_pre_llm_call(self) -> list[ChatCompletionMessageParam]:
        """LLM 호출 전에 Cache Control 블록을 적용합니다.

        Returns:
            cache_control 블록이 적용된 메시지 리스트
        """
        messages = copy.deepcopy(self.state.messages)
        return cast(
            list[ChatCompletionMessageParam],
            apply_cache_control_blocks(cast(list[dict[str, Any]], messages)),
        )


class OptimizedResearcherWorkflow(ResearcherWorkflow):
    """ModelSelector + OptimizedSearchAgent가 적용된 ResearcherWorkflow.

    최적화 내용:
    - ModelSelector로 Generation/Evaluation/Search 모델을 각각 자동 선택
    - _define_required_info: GENERATION 모델로 필요 정보 생성
    - SearchAgent → OptimizedSearchAgent (파라미터 제한 + 결과 필터링이 에이전트 내부에서 처리)
    """

    _search_model: str

    def __init__(self, model: str = "claude-4.5-haiku") -> None:
        _ = model
        selector = ModelSelector()
        # _define_required_info의 generation에 사용할 모델
        super().__init__(model=selector.select(TaskType.GENERATION).model)
        # search agent에 전달할 모델
        self._search_model = selector.select(TaskType.SEARCH_ORCHESTRATION).model
        self._required_info_evaluator = ScoredRequiredInfoEvaluator(
            model=selector.select(TaskType.EVALUATION).model,
        )

    @observe(capture_input=False, capture_output=False)
    async def _run_search_agents(
        self, section_research_results: dict[str, SectionResearch]
    ) -> dict[str, SectionResearch]:
        """OptimizedSearchAgent를 사용하여 병렬 검색을 실행하고, 결과를 필터링합니다.

        SearchAgent 대신 OptimizedSearchAgent를 사용하여
        파라미터 제한(max_iterations=7, 쿼리 5개, 결과 20개)을 적용합니다.
        검색 결과 필터링은 FilteringSearchTool이 매 search_web 호출마다 자동 수행합니다.

        Args:
            section_research_results: 필요 정보가 정의된 섹션별 리서치 결과

        Returns:
            리서치 결과가 채워지고 필터링된 섹션별 SectionResearch 딕셔너리
        """

        async def _run_single_search(
            section_title: str, section_research: SectionResearch
        ) -> tuple[str, SectionResearch, list[ReferenceDocument]]:
            agent = await OptimizedSearchAgent.setup(
                section_title=section_title,
                section_description=section_research.section_description,
                required_info=section_research.required_info,
                model=self._search_model,
            )
            await agent.run()

            result = section_research
            if agent.state.section_research is not None:
                result = agent.state.section_research
                result.research_complete = True

            return section_title, result, agent.state.reference_documents

        tasks = [
            _run_single_search(title, research)
            for title, research in section_research_results.items()
        ]
        results = await asyncio.gather(*tasks)

        updated_results: dict[str, SectionResearch] = {}
        for section_title, research, _ in results:
            updated_results[section_title] = research

        return updated_results


class OptimizedWriterAgent(WriterAgent):
    """ModelSelector + adaptive max_iterations가 적용된 WriterAgent.

    최적화 내용:
    - ModelSelector로 Generation/Evaluation 모델을 자동 선택
    - ScoredSectionEvaluator/ScoredReportEvaluator가 score 기반 passed 도출 (soft pass 내장)
    - Tool 내부 평가 루프가 score 기반 passed를 자동 활용하므로 에이전트 레벨 재평가 불필요
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        outline: Any,
        section_research: dict[str, Any],
        model: str = "claude-4.5-sonnet",
        max_iterations: int = 5,
    ) -> Self:
        selector = ModelSelector()
        _ = model  # ModelSelector가 모델을 자동 선택하므로 무시

        # 섹션 수에 따른 adaptive max_iterations 계산 (섹션당 2회 반복 보장)
        num_sections = len(outline.sections) if hasattr(outline, "sections") else 5
        adaptive_max_iterations = max(max_iterations, num_sections * 2)

        self = await super().setup(
            outline=outline,
            section_research=section_research,
            model=selector.select(TaskType.GENERATION).model,
            max_iterations=adaptive_max_iterations,
        )
        # WriteSectionTool/PolishReportTool 내부 evaluator를 Scored 버전으로 교체
        eval_model = selector.select(TaskType.EVALUATION).model
        for tool in self.tools:
            if isinstance(tool, WriteSectionTool):
                tool.evaluator = ScoredSectionEvaluator(model=eval_model)
            elif isinstance(tool, PolishReportTool):
                tool.evaluator = ScoredReportEvaluator(model=eval_model)
        return self

    async def _hook_pre_llm_call(self) -> list[ChatCompletionMessageParam]:
        """LLM 호출 전에 Cache Control 블록을 적용합니다.

        Returns:
            cache_control 블록이 적용된 메시지 리스트
        """
        messages = copy.deepcopy(self.state.messages)
        return cast(
            list[ChatCompletionMessageParam],
            apply_cache_control_blocks(cast(list[dict[str, Any]], messages)),
        )


# =============================================================================
# Optimized Orchestrator (모든 최적화 결합)
# =============================================================================


class OptimizedOrchestratorAgent(OrchestratorAgent):
    """모델 전환 + Cache Control이 적용된 OrchestratorAgent.

    두 가지 최적화를 동시에 적용:
    1. Model Selection: ModelSelector로 작업별 적절한 모델 선택 (sub-agent 교체)
    2. Cache Control: _hook_pre_llm_call()에서 캐시 블록 적용

    setup()에서 tools 리스트를 오버라이드하여 Optimized sub-agent 클래스를 주입합니다.
    _hook_pre_llm_call()에서 Cache Control을 적용합니다.
    """

    @classmethod
    @observe(capture_input=True, capture_output=True)
    async def setup(  # type: ignore[override]
        cls,
        user_request: str,
        max_iterations: int = 20,
    ) -> Self:
        """Optimized OrchestratorAgent를 생성합니다.

        ModelSelector로 Orchestration 모델을 자동 선택합니다.

        Args:
            user_request: 사용자의 리포트 요청
            max_iterations: 최대 반복 횟수

        Returns:
            초기화된 OptimizedOrchestratorAgent 인스턴스
        """
        selector = ModelSelector()

        self = await super().setup(
            user_request=user_request,
            model=selector.select(TaskType.ORCHESTRATION).model,
            max_iterations=max_iterations,
        )
        # Optimized sub-agent 클래스를 주입한 tools로 교체
        self.tools = [
            CallOutlinerTool(subagent_class=OptimizedOutlinerAgent),
            CallResearcherTool(workflow_class=OptimizedResearcherWorkflow),
            CallWriterTool(subagent_class=OptimizedWriterAgent),
            FinalAnswerTool(),
        ]
        return self

    async def _hook_pre_llm_call(self) -> list[ChatCompletionMessageParam]:
        """LLM 호출 전에 Cache Control 블록을 적용합니다.

        Returns:
            cache_control 블록이 적용된 메시지 리스트
        """
        messages = copy.deepcopy(self.state.messages)
        return cast(
            list[ChatCompletionMessageParam],
            apply_cache_control_blocks(cast(list[dict[str, Any]], messages)),
        )


# =============================================================================
# Helper 함수
# =============================================================================


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


async def run_optimized(user_request: str) -> RunResult:
    """모든 최적화가 적용된 OptimizedOrchestratorAgent를 실행합니다.

    최적화 내용:
    1. Cache Control (캐시 블록 적용)
    2. Model Selection (Evaluator에 haiku 사용)
    3. Loop Optimization (adaptive max_iterations)

    Args:
        user_request: 사용자의 리포트 요청

    Returns:
        RunResult: 실행 결과
    """
    selector = ModelSelector()
    result = RunResult(
        label="Optimized",
        agent_type="OptimizedOrchestratorAgent",
        optimizations=[
            f"Model Selection (Evaluator -> {selector.select(TaskType.EVALUATION).model})",
            "Cache Control (3-block strategy)",
            "Score-based passed derivation (evaluator 내장 soft pass)",
            "Adaptive max_iterations (섹션 수 기반)",
            "SearchAgent param limits (max_iterations=7, queries<=5, num_results=20)",
            f"Result filtering (LLM-based, model={selector.select(TaskType.RESULT_FILTERING).model})",
        ],
    )

    print("\n" + "=" * 70)
    print("Optimized - OptimizedOrchestratorAgent (All Optimizations)")
    print("=" * 70)

    agent = await OptimizedOrchestratorAgent.setup(
        user_request=user_request,
        max_iterations=20,
    )

    print(f"\n요청: {user_request}")
    print(f"Orchestration Model: {selector.select(TaskType.ORCHESTRATION).model}")
    print(f"Generation Model: {selector.select(TaskType.GENERATION).model}")
    print(f"Evaluator Model: {selector.select(TaskType.EVALUATION).model}")
    print(f"Search Orchestration Model: {selector.select(TaskType.SEARCH_ORCHESTRATION).model}")
    print("Cache Control: ON (3-block strategy)")
    print("Loop Optimization: ON (adaptive max_iterations)")
    print("SearchAgent: max_iterations=7, queries<=5, num_results=20")
    print(f"Result Filtering: ON (model={selector.select(TaskType.RESULT_FILTERING).model})")
    print("=" * 70 + "\n")

    print("Running optimized agent...\n")

    start_time = time.time()
    try:
        await agent.run()
    except Exception as e:
        print(f"\nOptimized 오류 발생: {e}")
        result.elapsed_time = time.time() - start_time
        return result

    result.elapsed_time = time.time() - start_time
    result.iteration_count = agent.state.iteration_count

    if agent.state.final_report:
        result.has_report = True
        result.report_title = agent.state.final_report.title
        result.report_sections = len(agent.state.final_report.sections)

    # 최종 리포트 출력
    print_report(agent)

    # cache_control 적용 정보 (마지막 호출 기준)
    cached_messages = apply_cache_control_blocks(cast(list[dict[str, Any]], agent.state.messages))
    print_cache_control_info(cached_messages)

    print(
        f"\nOptimized 완료! (iterations: {agent.state.iteration_count}, "
        f"time: {result.elapsed_time:.1f}s)"
    )
    print(f"현재 Phase: {agent.state.current_phase}")

    return result


# =============================================================================
# 메인 함수
# =============================================================================


async def main() -> None:
    """통합 최적화 데모 메인 함수.

    데모 흐름:
    1. Baseline 실행 (최적화 없음)
    2. Optimized 실행 (Cache Control + Model Selection + Loop Optimization)
    3. 비교 결과 출력
    """
    setup_langfuse()

    print("\n" + "=" * 70)
    print("Lecture 08-04: Cost Optimization Demo")
    print("=" * 70)

    # SERPER_API_KEY 확인
    if not os.environ.get("SERPER_API_KEY"):
        print("\n오류: SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Serper API 키는 https://serper.dev 에서 발급받을 수 있습니다.")
        print("\n사용법:")
        print("  export SERPER_API_KEY='your-api-key'")
        print("  rye run lec08-04")
        sys.exit(1)

    user_request = (
        "AI Trends in 2025: Agents, Multimodality, and Open Source에 대한 리포트를 작성해주세요."
    )

    await run_optimized(user_request)

    print("\n데모 완료!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
