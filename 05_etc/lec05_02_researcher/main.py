"""Lecture 05-02 통합 실행 예제 - Researcher Workflow 데모.

이 모듈은 ResearcherWorkflow의 동작을 시연하는 종합 예제입니다.
Outliner Agent가 생성한 아웃라인을 입력으로 받아, 각 섹션에 필요한 정보를
정의하고 SearchAgent를 병렬로 실행하여 정보를 수집합니다.

학습 포인트:
    1. 워크플로우 패턴 (Orchestrator 없이 결정론적 흐름)
       - Step 1: LLM 구조화 출력으로 필요 정보 정의 + Evaluator 피드백 루프
       - Step 2: 섹션별 SearchAgent 병렬 실행
       - Step 3: 참조 문서 중복 제거 (Deduplication)
    2. Evaluator 기반 피드백 루프
       - 필요 정보 정의 루프 (RequiredInfoEvaluator)

실행 방법:
    rye run lec05-02

리서치 흐름:
    Outline 입력 (OutlinerAgent 결과)
        └── ResearcherWorkflow.run()
              ├── Step 1: 필요 정보 정의 (LLM 구조화 출력)
              │     └── RequiredInfoEvaluator 평가 루프
              │           ├── 통과 → Step 2로 진행
              │           └── 미달 → 피드백과 함께 재정의
              ├── Step 2: 섹션별 SearchAgent 병렬 실행
              │     └── SearchAgent.run() × N (각 섹션별)
              │           ├── Web Search (병렬 쿼리)
              │           ├── (선택) Fetch 상세 콘텐츠
              │           └── submit_research로 리서치 제출
              └── Step 3: 참조 문서 중복 제거

참고:
    - ResearcherWorkflow: lecture/lec05_02_researcher/agent.py
    - SearchAgent: lecture/lec05_02_researcher/search_agent.py
    - RequiredInfoEvaluator: lecture/lec05_02_researcher/evaluator.py
    - Architecture: archiecture/researcher_agent.png
"""

import asyncio
import os
import sys

from lec05_01_outliner.schemas import Outline, OutlineSection
from lec05_02_researcher.agent import ResearcherWorkflow
from lec05_02_researcher.state import ResearcherState


async def main() -> None:
    """메인 데모 함수."""
    print("\n" + "=" * 80)
    print("Lecture 05-02: Researcher Workflow 데모")
    print("=" * 80)

    # SERPER_API_KEY 확인
    if not os.environ.get("SERPER_API_KEY"):
        print("\n오류: SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Serper API 키는 https://serper.dev 에서 발급받을 수 있습니다.")
        print("\n사용법:")
        print("  export SERPER_API_KEY='your-api-key'")
        print("  rye run lec05-02")
        sys.exit(1)

    # 데모 아웃라인 생성
    outline = create_demo_outline()

    print(f"\n아웃라인 제목: {outline.title}")
    print(f"섹션 수: {len(outline.sections)}")
    for i, section in enumerate(outline.sections, 1):
        print(f"  {i}. {section.title}")

    print("\nResearcherWorkflow를 실행합니다...")

    try:
        # ResearcherWorkflow 실행
        workflow = ResearcherWorkflow(model="claude-4.5-sonnet")

        print("\n" + "=" * 80)
        print("워크플로우 실행 과정")
        print("=" * 80)
        print("(필요 정보 정의 → Evaluator 평가 → 병렬 리서치 → 중복 제거)")
        print()

        state = await workflow.run(outline=outline)

        # 결과 출력
        print("\n" + "=" * 80)
        print("워크플로우 실행 완료")
        print("=" * 80)

        # 리서치 결과 출력
        print_research_results(state)

        print("\n" + "=" * 80)
        print("데모 완료!")
        print("=" * 80 + "\n")

    except Exception as e:
        print("\n" + "=" * 80)
        print("오류 발생")
        print("=" * 80)
        print(f"오류 메시지: {e}")
        print("\n일반적인 문제:")
        print("1. SERPER_API_KEY가 올바르게 설정되지 않음")
        print("2. 네트워크 연결 문제")
        print("3. API 할당량 초과")
        print("=" * 80 + "\n")
        sys.exit(1)


def print_research_results(state: ResearcherState) -> None:
    """리서치 결과를 보기 좋게 출력합니다.

    Args:
        state: ResearcherState 인스턴스
    """
    print("\n" + "=" * 80)
    print("리서치 결과")
    print("=" * 80 + "\n")

    for title, research in state.section_research_results.items():
        print(f"## {title}")
        print(f"   완료 여부: {'완료' if research.research_complete else '진행 중'}")
        print(f"   필요 정보 항목: {len(research.required_info)}개")

        # 필요 정보 항목 출력
        for i, info in enumerate(research.required_info, 1):
            status = "[covered]" if info.covered else "[pending]"
            print(f"     {i}. {status} {info.description}")

        fetched_count = sum(
            1 for doc in research.reference_documents if doc.content is not None
        )
        print(f"   참조 문서: {len(research.reference_documents)}개")
        print(f"   페치한 콘텐츠: {fetched_count}개")

        if research.summary:
            # 요약의 첫 200자만 출력
            summary_preview = research.summary[:200]
            if len(research.summary) > 200:
                summary_preview += "..."
            print(f"   요약: {summary_preview}")

        print()

    print("-" * 80)
    print(f"전체 참조 문서 수 (중복 제거): {len(state.reference_documents)}")

    all_complete = all(
        r.research_complete for r in state.section_research_results.values()
    )
    print(f"전체 리서치 완료: {all_complete}")
    print("=" * 80 + "\n")


def create_demo_outline() -> Outline:
    """데모용 아웃라인을 생성합니다.

    실제로는 OutlinerAgent가 생성하지만, 단독 데모를 위해
    하드코딩된 아웃라인을 제공합니다.

    Returns:
        데모용 Outline 객체
    """
    return Outline(
        title="2025년 생성형 AI 시장 동향",
        sections=[
            OutlineSection(
                title="글로벌 생성형 AI 시장 규모와 성장 전망",
                description=(
                    "2025년 현재 글로벌 생성형 AI 시장의 규모를 주요 시장 조사 기관의 "
                    "리포트를 기반으로 분석합니다. 시장 성장률, 투자 동향, "
                    "그리고 2030년까지의 전망을 포함합니다."
                ),
                subsections=[
                    "시장 규모 현황",
                    "투자 및 펀딩 동향",
                    "성장 전망 (2025-2030)",
                ],
            ),
            OutlineSection(
                title="주요 기업별 전략과 제품 분석",
                description=(
                    "OpenAI, Anthropic, Google, Meta 등 주요 플레이어의 최신 제품과 "
                    "전략을 비교 분석합니다. 각 기업의 시장 포지셔닝, "
                    "최근 발표된 모델, 그리고 차별화 전략을 다룹니다."
                ),
                subsections=[
                    "OpenAI (GPT 시리즈)",
                    "Anthropic (Claude 시리즈)",
                    "Google (Gemini 시리즈)",
                    "오픈소스 진영 (Meta, Mistral 등)",
                ],
            ),
            OutlineSection(
                title="핵심 기술 트렌드와 혁신",
                description=(
                    "2025년 생성형 AI 분야의 핵심 기술 트렌드를 분석합니다. "
                    "AI 에이전트, 멀티모달 AI, 소형 모델 최적화, "
                    "그리고 추론 능력 향상 등 주요 기술 방향을 다룹니다."
                ),
                subsections=[
                    "AI 에이전트 기술",
                    "멀티모달 AI",
                    "소형/경량 모델",
                    "추론 능력 향상",
                ],
            ),
        ],
    )


if __name__ == "__main__":
    asyncio.run(main())
