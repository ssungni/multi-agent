"""Lecture 05-03 통합 실행 예제 - Writer Agent 데모.

이 모듈은 WriterAgent의 동작을 시연하는 종합 예제입니다.
Outliner Agent가 생성한 아웃라인과 Researcher Agent가 수집한 리서치 결과를
입력으로 받아, 각 섹션을 작성하고 최종 리포트를 생성합니다.

학습 포인트:
    1. 섹션별 콘텐츠 작성 (Section Writing)
       - 리서치 데이터를 활용한 구조화된 섹션 작성
       - 출처 인용 처리
    2. 두 단계 Evaluator 기반 피드백 루프
       - Loop 1 (SectionEvaluator): 개별 섹션 품질 검증
         - 리서치 활용도, 인용 정확성, 가독성, description 커버리지
       - Loop 2 (ReportEvaluator): 전체 리포트 품질 검증
         - 문체 일관성, 논리적 흐름, 섹션 간 연결, 중복 제거
    3. WriterAgent의 종료 조건
       - report_evaluation_passed 또는 max_iterations 도달

실행 방법:
    rye run lec05-03

리포트 작성 흐름:
    Outline + SectionResearch 입력 (OutlinerAgent + ResearcherAgent 결과)
        └── WriterAgent.setup()
              └── WriterState 초기화
              └── Tools 등록 (WriteSectionTool, PolishReportTool)
        └── WriterAgent.run()
              └── 섹션별 콘텐츠 작성 (write_section)
                    └── SectionEvaluator 평가 [Loop 1]
                          ├── 통과 → 다음 섹션
                          └── 미달 → 피드백과 함께 재작성
              └── 모든 섹션 통과 후 리포트 통합 (polish_report)
                    └── ReportEvaluator 평가 [Loop 2]
                          ├── 통과 → 최종 리포트 완성
                          └── 미달 → 피드백 반영 후 재통합
        └── Final Report 출력

참고:
    - WriterAgent: lecture/lec05_03_writer/agent.py
    - SectionEvaluator: lecture/lec05_03_writer/evaluator.py
    - ReportEvaluator: lecture/lec05_03_writer/evaluator.py
    - Architecture: archiecture/writer_agent.md
"""

import asyncio
import sys

from lec04_02_tools.schemas import SearchResult
from lec05_01_outliner.schemas import Outline, OutlineSection
from lec05_02_researcher.schemas import RequiredInfo, SectionResearch
from lec05_03_writer.agent import WriterAgent


async def main() -> None:
    """메인 데모 함수."""
    print("\n" + "=" * 80)
    print("Lecture 05-03: Writer Agent 데모")
    print("=" * 80)

    # 데모 데이터 생성
    outline, section_research = create_demo_data()

    print(f"\n아웃라인 제목: {outline.title}")
    print(f"섹션 수: {len(outline.sections)}")
    for i, section in enumerate(outline.sections, 1):
        print(f"  {i}. {section.title}")

    print("\n리서치 결과:")
    for title, research in section_research.items():
        print(f"  {title}: 참조 문서 {len(research.reference_documents)}개, "
              f"요약 {len(research.summary)}자")

    print("\nWriterAgent를 초기화합니다...")

    try:
        # WriterAgent 설정
        agent = await WriterAgent.setup(
            outline=outline,
            section_research=section_research,
            model="claude-4.5-sonnet",
            max_iterations=20,
        )

        print("WriterAgent 실행 중...\n")
        print("=" * 80)
        print("에이전트 실행 과정")
        print("=" * 80)
        print("(섹션 작성 → 섹션 평가 → 리포트 통합 → 리포트 평가)")
        print()

        # 에이전트 실행
        await agent.run()

        # 결과 출력
        print("\n" + "=" * 80)
        print("에이전트 실행 완료")
        print("=" * 80)
        print(f"총 반복 횟수: {agent.state.iteration_count}")

        # 결과 출력
        print_results(agent)

        print("\n" + "=" * 80)
        print("데모 완료!")
        print("=" * 80 + "\n")

    except Exception as e:
        print("\n" + "=" * 80)
        print("오류 발생")
        print("=" * 80)
        print(f"오류 메시지: {e}")
        print("\n일반적인 문제:")
        print("1. LLM API 키가 올바르게 설정되지 않음")
        print("2. 네트워크 연결 문제")
        print("3. API 할당량 초과")
        print("=" * 80 + "\n")
        sys.exit(1)


def print_results(agent: WriterAgent) -> None:
    """Writer Agent 결과를 보기 좋게 출력합니다.

    Args:
        agent: WriterAgent 인스턴스
    """
    print("\n" + "=" * 80)
    print("작성 결과")
    print("=" * 80 + "\n")

    # 작성된 섹션 요약
    print("--- 작성된 섹션 ---")
    for title, section in agent.state.written_sections.items():
        feedback = agent.state.section_evaluation_feedback.get(title)
        status = "통과" if feedback is None else f"피드백: {feedback[:100]}..."
        print(f"  {title}")
        print(f"    콘텐츠 길이: {len(section.content)} 자")
        print(f"    인용 출처: {len(section.sources)} 개")
        print(f"    평가 상태: {status}")
        print()

    print(f"섹션 전체 평가 통과: {agent.state.sections_evaluation_passed}")

    # 최종 리포트
    if agent.state.final_report:
        report = agent.state.final_report
        print("\n--- 최종 리포트 ---")
        print(f"제목: {report.title}")
        print(f"섹션 수: {len(report.sections)}")
        print(f"참고 문헌: {len(report.references)} 개")

        # 리포트 본문 미리보기
        print("\n--- 리포트 미리보기 ---\n")
        for section in report.sections:
            print(f"## {section.title}")
            # 최대 300자만 출력
            preview = section.content[:300]
            if len(section.content) > 300:
                preview += "..."
            print(preview)
            print()

        print(f"리포트 평가 통과: {agent.state.report_evaluation_passed}")
        if agent.state.report_evaluation_feedback:
            print(f"리포트 평가 피드백: {agent.state.report_evaluation_feedback}")
    else:
        print("\n최종 리포트가 생성되지 않았습니다.")

    print("=" * 80 + "\n")


def create_demo_data() -> tuple[Outline, dict[str, SectionResearch]]:
    """데모용 아웃라인과 리서치 결과를 생성합니다.

    실제로는 OutlinerAgent와 ResearcherAgent가 생성하지만,
    단독 데모를 위해 하드코딩된 데이터를 제공합니다.

    Returns:
        (Outline, dict[str, SectionResearch]) 튜플
    """
    outline = Outline(
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

    section_research: dict[str, SectionResearch] = {
        "글로벌 생성형 AI 시장 규모와 성장 전망": SectionResearch(
            section_title="글로벌 생성형 AI 시장 규모와 성장 전망",
            section_description=(
                "2025년 현재 글로벌 생성형 AI 시장의 규모를 주요 시장 조사 기관의 "
                "리포트를 기반으로 분석합니다."
            ),
            required_info=[
                RequiredInfo(description="2025년 글로벌 생성형 AI 시장 규모 (달러)", covered=True),
                RequiredInfo(description="연간 성장률 (CAGR)", covered=True),
                RequiredInfo(description="주요 투자 라운드 및 펀딩 동향", covered=True),
            ],
            search_results=[
                SearchResult(
                    title="Generative AI Market Size 2025 - Grand View Research",
                    url="https://www.grandviewresearch.com/industry-analysis/generative-ai-market",
                    snippet=(
                        "The global generative AI market size was valued at $67.2 billion "
                        "in 2024 and is projected to grow at a CAGR of 36.7% from 2025 to 2030."
                    ),
                ),
                SearchResult(
                    title="AI Funding Report 2025 - CB Insights",
                    url="https://www.cbinsights.com/research/ai-funding-2025",
                    snippet=(
                        "AI startups raised $52.8 billion in 2024, with generative AI companies "
                        "accounting for 40% of total AI funding. Key rounds include Anthropic's "
                        "$4B from Amazon and xAI's $6B round."
                    ),
                ),
            ],
            fetched_contents={},
            summary=(
                "The global generative AI market reached $67.2B in 2024 with a projected "
                "CAGR of 36.7% through 2030. Major funding rounds in 2024 included "
                "Anthropic ($4B from Amazon) and xAI ($6B). AI startups raised $52.8B total "
                "in 2024, with gen AI representing 40% of all AI funding."
            ),
            research_complete=True,
        ),
        "주요 기업별 전략과 제품 분석": SectionResearch(
            section_title="주요 기업별 전략과 제품 분석",
            section_description=(
                "OpenAI, Anthropic, Google, Meta 등 주요 플레이어의 최신 제품과 "
                "전략을 비교 분석합니다."
            ),
            required_info=[
                RequiredInfo(description="OpenAI의 최신 모델 및 전략", covered=True),
                RequiredInfo(description="Anthropic의 Claude 시리즈 발전", covered=True),
                RequiredInfo(description="Google Gemini의 멀티모달 전략", covered=True),
                RequiredInfo(description="Meta의 오픈소스 LLM 전략", covered=True),
            ],
            search_results=[
                SearchResult(
                    title="OpenAI GPT-5 Launch and Enterprise Strategy",
                    url="https://openai.com/blog/gpt5-launch",
                    snippet=(
                        "OpenAI launched GPT-5 in early 2025 with significant improvements in "
                        "reasoning and code generation. Enterprise adoption grew 300% YoY."
                    ),
                ),
                SearchResult(
                    title="Anthropic Claude 4.5 - Safety-First AI",
                    url="https://www.anthropic.com/news/claude-4-5",
                    snippet=(
                        "Anthropic released Claude 4.5 with enhanced reasoning capabilities "
                        "and industry-leading safety features. Constitutional AI approach "
                        "continues to differentiate the company."
                    ),
                ),
                SearchResult(
                    title="Google Gemini Ultra 2.0 Multimodal AI",
                    url="https://blog.google/technology/ai/gemini-ultra-2",
                    snippet=(
                        "Google's Gemini Ultra 2.0 sets new benchmarks in multimodal "
                        "understanding, combining text, image, video, and code capabilities."
                    ),
                ),
            ],
            fetched_contents={},
            summary=(
                "Major players in 2025: OpenAI launched GPT-5 with 300% enterprise growth. "
                "Anthropic released Claude 4.5 with safety-first approach. Google's Gemini "
                "Ultra 2.0 leads multimodal AI. Meta continues open-source strategy with "
                "Llama 4 series."
            ),
            research_complete=True,
        ),
        "핵심 기술 트렌드와 혁신": SectionResearch(
            section_title="핵심 기술 트렌드와 혁신",
            section_description=(
                "2025년 생성형 AI 분야의 핵심 기술 트렌드를 분석합니다."
            ),
            required_info=[
                RequiredInfo(description="AI 에이전트 기술의 발전 현황", covered=True),
                RequiredInfo(description="멀티모달 AI 기술 동향", covered=True),
                RequiredInfo(description="소형/경량 모델 최적화 기술", covered=True),
                RequiredInfo(description="추론 능력 향상 기법", covered=True),
            ],
            search_results=[
                SearchResult(
                    title="AI Agents: The Next Frontier - McKinsey Report",
                    url="https://www.mckinsey.com/capabilities/quantumblack/our-insights/ai-agents",
                    snippet=(
                        "AI agents capable of autonomous task execution are emerging as "
                        "the next major paradigm. Enterprise adoption of AI agents grew "
                        "200% in 2024, with applications in customer service, coding, and research."
                    ),
                ),
                SearchResult(
                    title="Small Language Models: Efficiency Meets Performance",
                    url="https://arxiv.org/abs/2025.01234",
                    snippet=(
                        "Recent advances in model distillation and quantization have enabled "
                        "sub-3B parameter models to achieve performance comparable to much "
                        "larger models on many tasks. Key techniques include GPTQ, AWQ, and "
                        "structured pruning."
                    ),
                ),
            ],
            fetched_contents={},
            summary=(
                "Key tech trends in 2025: AI agents for autonomous task execution (200% "
                "enterprise adoption growth). Multimodal AI combining text, image, video. "
                "Small model optimization (sub-3B models matching larger ones via distillation). "
                "Improved reasoning through chain-of-thought and tree-of-thought techniques."
            ),
            research_complete=True,
        ),
    }

    return outline, section_research


if __name__ == "__main__":
    asyncio.run(main())
