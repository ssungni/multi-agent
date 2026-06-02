"""Lecture 08-05-01 실행 예제 - File-based Communication.

이 모듈은 파일 기반 커뮤니케이션 패턴을 시연합니다.
Sub-agent 결과를 파일로 저장하고, 파일 경로만 LLM에 전달하여
컨텍스트 윈도우를 절약하는 방법을 보여줍니다.

학습 포인트:
    1. 파일 기반 커뮤니케이션 패턴
       - Sub-agent 결과를 JSON 파일로 저장
       - LLM에는 요약 + 파일 경로만 전달
       - read_file 도구로 필요할 때만 전체 내용 조회

    2. Context Window 절약 효과
       - 전체 내용 대비 파일 경로만 전달 시 토큰 수 비교
       - 대규모 결과일수록 절약 효과가 큼

    3. OptimizedOrchestratorAgent 상속
       - 기존 최적화(ModelSelector, Cache Control)를 유지하면서
       - 도구만 FileComm 버전으로 교체

실행 방법:
    rye run lec08-05-01

참고:
    - OptimizedOrchestratorAgent: lecture/lec08_04_cost/main.py
    - CallOutlinerTool 등: lecture/lec06_01_orchestrator/tools.py
"""

import asyncio
import os
import sys

import tiktoken

from lec02_02_langfuse.observability import setup_langfuse
from lec06_01_orchestrator.main import print_report
from lec08_05_01_file_comm.agent import FileCommOrchestratorAgent

# 토큰 계산용 인코더
_enc = tiktoken.get_encoding("o200k_base")


def _count_tokens(text: str) -> int:
    """텍스트의 토큰 수를 계산합니다."""
    return len(_enc.encode(text))


async def main() -> None:
    """파일 기반 커뮤니케이션 데모 메인 함수."""
    setup_langfuse()

    print("=" * 70)
    print("Lecture 08-05-01: File-based Communication Demo")
    print("=" * 70)

    # SERPER_API_KEY 확인
    if not os.environ.get("SERPER_API_KEY"):
        print("\n오류: SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("Serper API 키는 https://serper.dev 에서 발급받을 수 있습니다.")
        print("\n사용법:")
        print("  export SERPER_API_KEY='your-api-key'")
        print("  rye run lec08-05-01")
        sys.exit(1)

    user_request = (
        "AI Trends in 2025: Agents, Multimodality, and Open Source에 대한 리포트를 작성해주세요."
    )

    agent = await FileCommOrchestratorAgent.setup(
        user_request=user_request,
        max_iterations=20,
    )

    print(f"\n요청: {user_request}")
    print(f"Model: {agent.model}")
    print(f"Tools: {[tool.name for tool in agent.tools]}")
    if agent.workspace:
        print(f"Workspace: {agent.workspace.workspace_dir}")
    print("=" * 70 + "\n")

    print("Running agent...\n")

    try:
        await agent.run()
    except Exception as e:
        print(f"\n오류 발생: {e}")
        sys.exit(1)

    # 최종 리포트 출력
    print_report(agent)

    # 워크스페이스 파일 목록 및 크기 출력
    if agent.workspace:
        print("\n" + "=" * 70)
        print("Workspace Files")
        print("=" * 70)

        total_file_tokens = 0
        total_path_tokens = 0

        for filepath in agent.workspace.list_files():
            file_size = filepath.stat().st_size
            file_content = filepath.read_text(encoding="utf-8")
            file_tokens = _count_tokens(file_content)
            path_tokens = _count_tokens(str(filepath))

            total_file_tokens += file_tokens
            total_path_tokens += path_tokens

            print(f"  {filepath.name}: {file_size:,} bytes ({file_tokens:,} tokens)")

        # 파일 경로 vs 전체 내용의 토큰 수 비교
        print("\n토큰 비교:")
        print(f"  전체 내용을 컨텍스트에 넣을 경우: {total_file_tokens:,} tokens")
        print(f"  파일 경로만 전달할 경우:          {total_path_tokens:,} tokens")
        if total_file_tokens > 0:
            savings = ((total_file_tokens - total_path_tokens) / total_file_tokens) * 100
            print(f"  절약률: {savings:.1f}%")

    print(f"\n완료! (iterations: {agent.state.iteration_count})")
    print(f"현재 Phase: {agent.state.current_phase}")

    print("\n학습 요약:")
    print("  1. Sub-agent 결과를 파일로 저장하여 컨텍스트 윈도우 절약")
    print("  2. 파일 경로만 LLM에 전달하고, read_file로 필요시 조회")
    print("  3. OptimizedOrchestratorAgent 상속으로 기존 최적화 유지")
    print("  4. 대규모 결과일수록 파일 기반 방식의 토큰 절약 효과가 큼")


if __name__ == "__main__":
    asyncio.run(main())
