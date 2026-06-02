"""02-02 강의 실행 예제: LiteLLM + Langfuse Integration Demo

이 스크립트는 LiteLLM Router와 Langfuse 모니터링을 통합하여
멀티 프로바이더 LLM 호출을 데모합니다.
Report Generation 시나리오에서 아웃라인 생성 작업을 Langfuse로 모니터링합니다.

학습 포인트:
    1. LiteLLM Router로 여러 LLM 프로바이더를 단일 인터페이스로 통합
       - 하나의 Router 인스턴스로 OpenAI, Anthropic, Google 모델을 동일하게 호출
    2. Langfuse를 통한 LLM 호출 모니터링 및 성능 분석
       - @observe 데코레이터를 사용한 자동 트레이싱
       - 모델별 응답 시간, 토큰 사용량 비교
    3. Report Generation 시나리오에서 각 모델의 아웃라인 생성 응답 비교
       - 동일한 리포트 주제에 대해 각 모델의 응답 차이를 Langfuse에서 분석

실행 방법:
    rye run python -m lec02_02_langfuse.main

멀티 프로바이더 비교 + Langfuse 모니터링 흐름:
    setup_langfuse()
        └── Langfuse 초기화 및 LiteLLM 콜백 등록
    demo_multi_provider_calls()
        └── @observe → Langfuse trace 생성
        └── call_model("gpt-5", prompt)
              └── @observe → Langfuse observation
              └── LiteLLM Router → OpenAI API
        └── call_model("claude-4.5-sonnet", prompt)
              └── @observe → Langfuse observation
              └── LiteLLM Router → Anthropic API
        └── call_model("gemini-3-flash", prompt)
              └── @observe → Langfuse observation
              └── LiteLLM Router → Google AI API
        └── Langfuse 대시보드에서 모델별 비교 가능

참고:
    - LiteLLM Router: lecture/lec02_01_litellm/router.py
    - Langfuse Setup: lecture/lec02_02_langfuse/observability.py
"""

import asyncio

from lec02_02_langfuse.observability import langfuse_context, observe, setup_langfuse
from lec02_02_langfuse.router import router


async def main() -> None:
    """메인 함수: 멀티 프로바이더 호출 데모를 실행합니다."""
    print("\n" + "=" * 80)
    print("Lecture 02-02: LiteLLM + Langfuse Integration Demo")
    print("=" * 80)
    print("\n이 데모는 여러 LLM 프로바이더 (OpenAI, Claude, Gemini)를 통합 호출하여")
    print("Report Generation 시나리오에서 아웃라인 생성 능력을 비교합니다.")
    print("모든 호출은 Langfuse에 자동으로 기록됩니다.")
    print("https://cloud.langfuse.com 에서 trace를 확인할 수 있습니다.\n")

    await demo_multi_provider_calls()

    print("\n" + "=" * 80)
    print("데모 완료!")
    print("=" * 80)
    print("\nLangfuse 대시보드에서 다음 정보를 확인할 수 있습니다:")
    print("  - 각 모델별 응답 시간 비교")
    print("  - 토큰 사용량 및 비용")
    print("  - 전체 trace 흐름 시각화")
    print("\nURL: https://cloud.langfuse.com")
    print("\n")


@observe(capture_input=False, capture_output=False)
async def demo_multi_provider_calls() -> None:
    """여러 프로바이더 모델로 동일한 리포트 아웃라인 생성 프롬프트를 호출하는 예제.

    GPT-5, Claude 4.5 Sonnet, Gemini 3 Flash에 동일한 리포트 아웃라인 생성 요청을
    보내고 각 모델의 응답을 비교합니다.
    모든 호출은 Langfuse에 기록되어 대시보드에서 비교할 수 있습니다.

    학습 목표:
        - LiteLLM Router를 사용하면 다른 프로바이더의 모델을 동일한 인터페이스로 호출 가능
        - Report Generation 시나리오에서 각 모델의 아웃라인 구조 차이 이해
        - Langfuse 대시보드에서 모델별 응답 시간과 토큰 사용량 비교

    예상 출력:
        - 각 모델이 동일한 리포트 주제에 대해 어떻게 다른 아웃라인을 제안하는지 확인
        - Langfuse 대시보드에서 모델별 응답 시간과 토큰 사용량 비교
    """
    langfuse_context.update_current_trace(
        name="multi_provider_demo",
        metadata={"demo_type": "multi_provider_outline_comparison"},
    )

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


@observe(capture_input=False, capture_output=True)
async def call_model(model_name: str, prompt: str) -> str:
    """특정 모델로 LLM 호출을 수행합니다.

    이 함수는 LiteLLM Router를 통해 지정된 모델에 프롬프트를 전송하고,
    응답을 반환합니다. 모든 호출은 Langfuse에 자동으로 기록됩니다.

    Args:
        model_name: 호출할 모델 이름 (예: "gpt-5", "claude-4.5-sonnet", "gemini-3-flash")
        prompt: LLM에 전달할 프롬프트

    Returns:
        str: LLM의 응답 텍스트

    학습 포인트:
        - @observe 데코레이터로 Langfuse에 자동 트레이싱
        - langfuse_context로 메타데이터 추가 (프롬프트 길이, 응답 길이 등)
        - LiteLLM Router의 acompletion API 사용법
    """
    langfuse_context.update_current_observation(
        name=f"call_{model_name}",
    )

    response = await router.acompletion(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        metadata={
            "trace_id": langfuse_context.get_current_trace_id(),
            "parent_observation_id": langfuse_context.get_current_observation_id(),
            "generation_name": f"llm_call_{model_name}",
        },
    )

    result = response.choices[0].message.content or ""  # type: ignore

    langfuse_context.update_current_observation(
        metadata={
            "model": model_name,
            "prompt_length": len(prompt),
            "response_length": len(result),
            "finish_reason": response.choices[0].finish_reason,
        },
    )

    return result


if __name__ == "__main__":
    # Langfuse 초기화
    setup_langfuse()

    asyncio.run(main())
