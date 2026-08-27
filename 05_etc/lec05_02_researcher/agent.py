"""Researcher Workflow 구현.

아웃라인의 각 섹션에 대해 필요한 정보를 수집하는 ResearcherWorkflow를 정의합니다.
Orchestrator 없이 워크플로우 형태로 구현합니다:

1. 필요 정보 정의 (LLM 구조화 출력 + Evaluator 피드백 루프)
2. 섹션별 SearchAgent 병렬 실행
3. 결과 중복 제거 (Deduplication)
"""

import asyncio
import logging

from langfuse.decorators import langfuse_context, observe

from lec02_02_langfuse.router import router
from lec04_02_tools.schemas import ReferenceDocument
from lec05_01_outliner.schemas import Outline
from lec05_02_researcher.evaluator import RequiredInfoEvaluator
from lec05_02_researcher.prompts import DEFINE_REQUIRED_INFO_PROMPT
from lec05_02_researcher.schemas import (
    RequiredInfoDefinition,
    SectionResearch,
)
from lec05_02_researcher.search_agent import SearchAgent
from lec05_02_researcher.state import ResearcherState

logger = logging.getLogger(__name__)

# 필요 정보 정의 Evaluator 피드백 루프 최대 반복 횟수
MAX_DEFINE_ITERATIONS = 3


class ResearcherWorkflow:
    """아웃라인 섹션별로 정보를 수집하는 워크플로우.

    Orchestrator 패턴 대신 결정론적 워크플로우로 구현합니다:

    1. **필요 정보 정의**: LLM 구조화 출력으로 각 섹션의 필요 정보를 정의
       - Evaluator 피드백 루프: 평가 미달 시 피드백을 반영하여 재정의
    2. **병렬 리서치**: 각 섹션을 SearchAgent에 위임하여 병렬 실행
    3. **중복 제거**: 수집된 참조 문서의 URL 기반 중복 제거

    Attributes:
        model: 사용할 LLM 모델 이름
        state: 워크플로우 실행 결과 상태

    Example:
        >>> workflow = ResearcherWorkflow(model="claude-4.5-sonnet")
        >>> state = await workflow.run(outline=outline)
        >>> for title, research in state.section_research_results.items():
        ...     print(f"{title}: {len(research.reference_documents)} results")
    """

    def __init__(self, model: str = "claude-4.5-sonnet") -> None:
        self.model = model
        self.state = ResearcherState()
        self._required_info_evaluator = RequiredInfoEvaluator(model=model)

    @observe(capture_input=True, capture_output=True)
    async def run(self, outline: Outline) -> ResearcherState:
        """워크플로우를 실행합니다.

        Args:
            outline: Outliner Agent가 생성한 아웃라인

        Returns:
            ResearcherState: 워크플로우 실행 결과
        """
        self.state.outline = outline

        # Step 1: 필요 정보 정의 (LLM + Evaluator 피드백 루프)
        section_research_results = await self._define_required_info(outline)
        self.state.section_research_results = section_research_results

        # Step 2: 섹션별 SearchAgent 병렬 실행
        section_research_results = await self._run_search_agents(section_research_results)
        self.state.section_research_results = section_research_results

        # Step 3: 참조 문서 중복 제거
        self.state.reference_documents = self._deduplicate_references(section_research_results)

        return self.state

    @observe(capture_input=True, capture_output=True)
    async def _define_required_info(self, outline: Outline) -> dict[str, SectionResearch]:
        """각 섹션에 대해 필요 정보를 정의합니다.

        LLM 구조화 출력으로 필요 정보를 정의하고, Evaluator가 평가합니다.
        평가 미달 시 피드백을 반영하여 재정의합니다 (최대 MAX_DEFINE_ITERATIONS회).

        Args:
            outline: 리서치 대상 아웃라인

        Returns:
            섹션 제목을 키로 하는 SectionResearch 딕셔너리
        """
        outline_json = outline.model_dump_json(indent=2)
        feedback = ""

        for iteration in range(MAX_DEFINE_ITERATIONS):
            # 피드백 섹션 구성
            feedback_section = ""
            if feedback:
                feedback_section = (
                    f"Previous evaluation feedback (please address these issues):\n{feedback}"
                )

            # LLM 구조화 출력 호출
            prompt = DEFINE_REQUIRED_INFO_PROMPT.format(
                outline_json=outline_json,
                feedback_section=feedback_section,
            )

            definition: RequiredInfoDefinition = await router.acompletion_with_response_model(
                response_model=RequiredInfoDefinition,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                metadata={
                    "existing_trace_id": langfuse_context.get_current_trace_id(),
                    "parent_observation_id": langfuse_context.get_current_observation_id(),
                },
            )

            # SectionResearch 딕셔너리 생성
            section_research_results: dict[str, SectionResearch] = {}
            for section_def in definition.sections[: len(outline.sections)]:
                # 아웃라인에서 섹션 설명 찾기
                section_description = ""
                for section in outline.sections:
                    if section.title == section_def.section_title:
                        section_description = section.description
                        break

                section_research_results[section_def.section_title] = SectionResearch(
                    section_title=section_def.section_title,
                    section_description=section_description,
                    required_info=section_def.required_info,
                )

            # Evaluator 평가
            evaluation_result = await self._required_info_evaluator.evaluate(
                outline=outline,
                section_research_results=section_research_results,
            )

            if evaluation_result.passed:
                logger.info("Required info evaluation passed (iteration %d)", iteration + 1)
                return section_research_results

            # 평가 미달 시 피드백 저장 후 재시도
            feedback = evaluation_result.feedback
            logger.info(
                "Required info evaluation failed (iteration %d): %s",
                iteration + 1,
                feedback,
            )

        # 최대 반복 후에도 미달이면 마지막 결과 사용
        logger.warning(
            "Required info evaluation did not pass after %d iterations, "
            "proceeding with last result",
            MAX_DEFINE_ITERATIONS,
        )
        return section_research_results

    @observe(capture_input=False, capture_output=False)
    async def _run_search_agents(
        self, section_research_results: dict[str, SectionResearch]
    ) -> dict[str, SectionResearch]:
        """각 섹션에 대해 SearchAgent를 병렬로 실행합니다.

        Args:
            section_research_results: 필요 정보가 정의된 섹션별 리서치 결과

        Returns:
            리서치 결과가 채워진 섹션별 SectionResearch 딕셔너리
        """

        async def _run_single_search(
            section_title: str, section_research: SectionResearch
        ) -> tuple[str, SectionResearch, list[ReferenceDocument]]:
            """개별 섹션의 SearchAgent를 실행합니다."""
            agent = await SearchAgent.setup(
                section_title=section_title,
                section_description=section_research.section_description,
                required_info=section_research.required_info,
                model=self.model,
            )
            await agent.run()

            # 결과 추출
            result = section_research
            if agent.state.section_research is not None:
                result = agent.state.section_research
                result.research_complete = True

            return section_title, result, agent.state.reference_documents

        # 모든 섹션에 대해 병렬 실행
        tasks = [
            _run_single_search(title, research)
            for title, research in section_research_results.items()
        ]
        results = await asyncio.gather(*tasks)

        # 결과 병합
        updated_results: dict[str, SectionResearch] = {}
        for section_title, research, _ in results:
            updated_results[section_title] = research

        return updated_results

    @staticmethod
    def _deduplicate_references(
        section_research_results: dict[str, SectionResearch],
    ) -> list[ReferenceDocument]:
        """모든 섹션의 참조 문서를 수집하고 URL 기반으로 중복을 제거합니다.

        Args:
            section_research_results: 섹션별 리서치 결과

        Returns:
            중복 제거된 참조 문서 리스트
        """
        seen_urls: set[str] = set()
        deduplicated: list[ReferenceDocument] = []

        for research in section_research_results.values():
            for doc in research.reference_documents:
                if doc.url not in seen_urls:
                    seen_urls.add(doc.url)
                    deduplicated.append(doc)

        logger.info(
            "Deduplication: %d unique references from %d total",
            len(deduplicated),
            sum(len(r.reference_documents) for r in section_research_results.values()),
        )
        return deduplicated
