"""Lecture 04-02 통합 실행 예제 - Common Tools 데모.

이 모듈은 SearchTool과 FetchTool의 동작을 시연하는 종합 예제입니다.
Serper API를 통한 웹 검색과 BeautifulSoup을 통한 콘텐츠 추출을 보여줍니다.

학습 포인트:
    1. SearchTool 사용법
       - 복수 쿼리 동시 검색
       - 검색 결과 포맷팅
    2. FetchTool 사용법
       - URL에서 메인 콘텐츠 추출
       - BeautifulSoup 기반 파싱
실행 방법:
    rye run lec04-02

환경 변수:
    SERPER_API_KEY: Serper API 키 (https://serper.dev)

참고:
    - SearchTool: lecture/lec04_02_tools/search.py
    - FetchTool: lecture/lec04_02_tools/fetch.py
    - BaseTool: lecture/lec04_01_base_agent/tool.py
"""

import asyncio
import os
import sys

from lec04_01_base_agent.state import BaseAgentState
from lec04_02_tools.fetch import FetchTool
from lec04_02_tools.schemas import ReferenceDocument
from lec04_02_tools.search import SearchTool


class DemoState(BaseAgentState):
    """도구 데모를 위한 상태 클래스.

    SearchTool과 FetchTool이 필요로 하는 속성을 포함합니다.

    Attributes:
        reference_documents: 검색 결과로 수집된 참조 문서 리스트
        document_full_text_map: URL을 키로 하고 페치한 전체 텍스트를 값으로 하는 맵
    """

    reference_documents: list[ReferenceDocument] = []
    document_full_text_map: dict[str, str] = {}


async def demo_search_tool(state: "DemoState") -> None:
    """SearchTool 사용법을 시연합니다.

    Args:
        state: 데모 상태 객체
    """
    print("\n" + "=" * 80)
    print("1. SearchTool 데모")
    print("=" * 80 + "\n")

    search_tool = SearchTool[DemoState]()

    # 웹 검색 실행
    print("검색 쿼리: ['AI agent 2024', 'LangChain tutorial']")
    print("검색 중...\n")

    result = await search_tool.call(
        state=state,
        tool_call_id="demo_search",
        arguments={
            "queries": ["AI agent 2024", "LangChain tutorial"],
            "num_results": 3,
        },
    )

    # 결과 출력
    print("검색 결과:")
    print("-" * 80)
    print(result.content)

    # 상태에 저장된 참조 문서 확인
    print(f"\n상태에 저장된 참조 문서 수: {len(state.reference_documents)}")



async def demo_fetch_tool(state: "DemoState") -> None:
    """FetchTool 사용법을 시연합니다.

    Args:
        state: 데모 상태 객체
    """
    print("\n" + "=" * 80)
    print("2. FetchTool 데모")
    print("=" * 80 + "\n")

    fetch_tool = FetchTool[DemoState]()

    # reference_documents에서 첫 번째 URL 선택
    if not state.reference_documents:
        print("검색 결과가 없어 FetchTool을 테스트할 수 없습니다.")
        return

    target_url = state.reference_documents[0].url
    print(f"페치할 URL: {target_url}")
    print("콘텐츠 추출 중...\n")

    try:
        result = await fetch_tool.call(
            state=state,
            tool_call_id="demo_fetch",
            arguments={"url": target_url},
        )

        # 결과 출력 (처음 500자만)
        content_preview = result.content[:500] if len(result.content) > 500 else result.content
        truncated = "..." if len(result.content) > 500 else ""

        print("추출된 콘텐츠 (처음 500자):")
        print("-" * 80)
        print(content_preview + truncated)
        print("\n" + "-" * 80)
        print(f"전체 콘텐츠 길이: {len(result.content)} 자")

        # 상태의 document_full_text_map 확인
        print(f"상태에 캐싱된 문서 수: {len(state.document_full_text_map)}")

    except Exception as e:
        print(f"FetchTool 실행 중 오류: {e}")
        print("일부 웹사이트는 봇 접근을 차단할 수 있습니다.")


async def main() -> None:
    """메인 데모 함수."""
    print("\n" + "=" * 80)
    print("Lecture 04-02: Common Tools 데모")
    print("=" * 80)

    # SERPER_API_KEY 확인
    if not os.environ.get("SERPER_API_KEY"):
        print("\n오류: SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Serper API 키는 https://serper.dev 에서 발급받을 수 있습니다.")
        print("\n사용법:")
        print("  export SERPER_API_KEY='your-api-key'")
        print("  rye run lec04-02")
        sys.exit(1)

    # 데모 상태 초기화
    state = DemoState(model="gpt-4")

    # SearchTool 데모
    await demo_search_tool(state)

    # FetchTool 데모
    await demo_fetch_tool(state)

    print("\n" + "=" * 80)
    print("데모 완료!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
