"""02-01 강의 실행 예제: LiteLLM Multi-Provider Routing Demo

이 스크립트는 LiteLLM Router를 사용하여 멀티 프로바이더 LLM 호출을 데모합니다.
Report Generation Agent 시나리오에서 여러 모델의 아웃라인 생성 능력을 비교합니다.

학습 포인트:
    1. LiteLLM Router로 여러 LLM 프로바이더를 단일 인터페이스로 통합
       - 하나의 Router 인스턴스로 OpenAI, Anthropic, Google 모델을 동일하게 호출
    2. Report Generation 시나리오에서 각 모델의 아웃라인 생성 응답 비교
       - 동일한 리포트 주제에 대해 각 모델이 어떤 구조의 아웃라인을 제안하는지 비교
    3. Fallback 전략의 작동 방식
       - 특정 프로바이더 실패 시 다른 프로바이더로 자동 전환

실행 방법:
    rye run python -m lec02_01_litellm.main

멀티 프로바이더 비교 흐름:
    User Input ("AI 트렌드 리포트 아웃라인 생성")
        └── call_model("gpt-5", prompt)
              └── LiteLLM Router → OpenAI API
        └── call_model("claude-4.5-sonnet", prompt)
              └── LiteLLM Router → Anthropic API
        └── call_model("gemini-3-flash", prompt)
              └── LiteLLM Router → Google AI API
        └── 각 모델의 아웃라인 응답 비교

참고:
    - LiteLLM Router: lecture/lec02_01_litellm/router.py
    - LLM Config: lecture/lec02_01_litellm/config.py
"""

import asyncio

from lec02_01_litellm.router import router


async def main() -> None:
    """메인 함수: 멀티 프로바이더 호출 데모를 실행합니다."""
    print("\n" + "=" * 80)
    print("Lecture 02-01: LiteLLM Multi-Provider Routing Demo")
    print("=" * 80)
    print("\n이 데모는 여러 LLM 프로바이더 (OpenAI, Claude, Gemini)를 통합 호출하여")
    print("Report Generation 시나리오에서 아웃라인 생성 능력을 비교합니다.\n")

    await demo_multi_provider_calls()

    print("\n" + "=" * 80)
    print("데모 완료!")
    print("=" * 80)
    print("\n학습 포인트:")
    print("  - LiteLLM Router를 통한 멀티 프로바이더 통합")
    print("  - 동일한 API 인터페이스로 다양한 LLM 호출")
    print("  - Report Generation 시나리오에서 모델별 아웃라인 구조 차이 이해")
    print("\n")


async def demo_multi_provider_calls() -> None:
    """여러 프로바이더 모델로 동일한 리포트 아웃라인 생성 프롬프트를 호출하는 예제.

    GPT-5, Claude 4.5 Sonnet, Gemini 3 Flash에 동일한 리포트 아웃라인 생성 요청을
    보내고 각 모델의 응답을 비교합니다.

    학습 목표:
        - LiteLLM Router를 사용하면 다른 프로바이더의 모델을 동일한 인터페이스로 호출 가능
        - Report Generation 시나리오에서 각 모델의 아웃라인 구조 차이 이해
        - 작업 유형에 따른 최적 모델 선택 기준 수립

    예상 출력:
        - 각 모델이 동일한 리포트 주제에 대해 어떻게 다른 아웃라인을 제안하는지 확인
    """
    prompt = (
        "Generate a brief outline (3-5 sections) for a report on "
        "'AI Trends in 2025: Agents, Multimodality, and Open Source'. "
        "For each section, provide a title and a one-sentence description."
    )

    print("\n" + "=" * 80)
    print("멀티 프로바이더 호출 (동일 프롬프트, 다른 모델)")
    print("=" * 80)
    print(f"\nPrompt: {prompt}\n")

    models = ["gpt-5", "claude-4.5-sonnet", "gemini-3-flash"]

    for model in models:
        print(f"\n[{model}]")
        print("-" * 80)
        try:
            response = await call_model(model, prompt)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")


async def call_model(model_name: str, prompt: str) -> str:
    """특정 모델로 LLM 호출을 수행합니다.

    이 함수는 LiteLLM Router를 통해 지정된 모델에 프롬프트를 전송하고,
    응답을 반환합니다.

    Args:
        model_name: 호출할 모델 이름 (예: "gpt-5", "claude-4.5-sonnet", "gemini-3-flash")
        prompt: LLM에 전달할 프롬프트

    Returns:
        str: LLM의 응답 텍스트

    학습 포인트:
        - LiteLLM Router의 acompletion API 사용법
        - 여러 프로바이더를 동일한 인터페이스로 호출
    """
    response = await router.acompletion(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content or ""  # type: ignore


if __name__ == "__main__":
    asyncio.run(main())
