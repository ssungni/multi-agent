"""Lecture 05-01 통합 실행 예제 - Outliner Agent 데모.

이 모듈은 OutlinerAgent의 동작을 시연하는 종합 예제입니다.
주어진 주제에 대해 웹 검색을 수행하고 구조화된 아웃라인을 생성합니다.

학습 포인트:
    1. Query Expansion을 통한 검색 쿼리 다양화
       - 단일 주제를 여러 관점의 쿼리로 확장
       - 정보 커버리지 극대화
    2. 두 가지 피드백 루프의 동작 이해
       - Orchestrator 주도 루프: 정보 충분성 판단
       - Evaluator 주도 루프: 아웃라인 품질 검증
    3. OutlineEvaluator의 평가 기준
       - 섹션 개수 (3~7개)
       - Description 구체성
       - 논리적 흐름

실행 방법:
    rye run lec05-01

아웃라인 생성 흐름:
    User Input ("2024년 생성형 AI 시장 동향")
        └── OutlinerAgent.setup()
              └── OutlinerState 초기화
              └── Tools 등록 (SearchTool, FetchTool, GenerateOutlineTool)
        └── OutlinerAgent.run()
              └── Query Expansion
                    └── ["생성형 AI 시장 규모 2024", "ChatGPT Claude 경쟁", ...]
              └── Web Search (병렬)
              └── (선택) Fetch 상세 콘텐츠
              └── Generate Outline
              └── OutlineEvaluator 평가
                    ├── 통과 → 종료
                    └── 미달 → 피드백과 함께 재생성
        └── Final Outline 출력

참고:
    - OutlinerAgent: lecture/lec05_01_outliner/agent.py
    - OutlineEvaluator: lecture/lec05_01_outliner/evaluator.py
    - Architecture: architecture/outliner_agent.md
"""

import asyncio
import os
import sys

from lec05_01_outliner.agent import OutlinerAgent


async def main() -> None:
    """메인 데모 함수."""
    print("\n" + "=" * 80)
    print("Lecture 05-01: Outliner Agent 데모")
    print("=" * 80)

    # SERPER_API_KEY 확인
    if not os.environ.get("SERPER_API_KEY"):
        print("\n오류: SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Serper API 키는 https://serper.dev 에서 발급받을 수 있습니다.")
        print("\n사용법:")
        print("  export SERPER_API_KEY='your-api-key'")
        print("  rye run lec05-01")
        sys.exit(1)

    # 데모 주제
    topic = "2025년 생성형 AI 시장 동향"

    print(f"\n주제: {topic}")
    print("\nOutlinerAgent를 초기화합니다...")

    try:
        # OutlinerAgent 설정
        agent = await OutlinerAgent.setup(
            topic=topic,
            model="claude-4.5-sonnet",
            max_iterations=10,
        )

        print("OutlinerAgent 실행 중...\n")
        print("=" * 80)
        print("에이전트 실행 과정")
        print("=" * 80)
        print("(Query Expansion → Web Search → Outline 생성 → 평가)")
        print()

        # 에이전트 실행
        await agent.run()

        # 결과 출력
        print("\n" + "=" * 80)
        print("에이전트 실행 완료")
        print("=" * 80)
        print(f"총 반복 횟수: {agent.state.iteration_count}")
        print(f"수집된 검색 결과 수: {len(agent.state.reference_documents)}")

        # 아웃라인 출력
        print_outline(agent)

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


def print_outline(agent: OutlinerAgent) -> None:
    """생성된 아웃라인을 보기 좋게 출력합니다.

    Args:
        agent: OutlinerAgent 인스턴스
    """
    if not agent.state.outline:
        print("아웃라인이 생성되지 않았습니다.")
        return

    outline = agent.state.outline

    print("\n" + "=" * 80)
    print("생성된 아웃라인")
    print("=" * 80 + "\n")
    print(f"제목: {outline.title}")
    print(f"섹션 개수: {len(outline.sections)}")
    print("\n" + "-" * 80 + "\n")

    for i, section in enumerate(outline.sections, 1):
        print(f"{i}. {section.title}")
        print(f"   설명: {section.description}")

        if section.subsections:
            print("   하위 섹션:")
            for subsection in section.subsections:
                print(f"   - {subsection}")

        print()

    print("-" * 80)
    print(f"평가 통과: {agent.state.evaluation_passed}")
    if agent.state.evaluation_feedback:
        print(f"평가 피드백: {agent.state.evaluation_feedback}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
