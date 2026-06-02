"""LiteLLM Router 설정 모듈.

멀티 프로바이더 LLM 라우팅을 위한 LiteLLM Router 래퍼를 제공합니다.
OpenAI, Claude, Gemini를 지원하며 자동 fallback 전략을 포함합니다.

Usage Example:
    from lec02_01_litellm.router import router

    response = await router.acompletion(
        model="claude-4.5-sonnet",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

Available models:
    - "gpt-5": GPT-5 (OpenAI)
    - "gpt-5-mini": GPT-5 Mini (OpenAI)
    - "gpt-4.1-mini": GPT-4.1 Mini (OpenAI)
    - "claude-4.5-sonnet": Claude 4.5 Sonnet (Anthropic)
    - "claude-4.5-haiku": Claude 4.5 Haiku (Anthropic)
    - "claude-4.5-opus": Claude 4.5 Opus (Anthropic)
    - "gemini-3-flash": Gemini 3 Flash (Google)
    - "gemini-3-pro": Gemini 3 Pro (Google)

Fallback strategy:
    - gpt-5 → claude-4.5-sonnet → gemini-3-flash
    - claude-4.5-sonnet → gpt-5 → gemini-3-flash
    - gemini-3-flash → gpt-5 → claude-4.5-sonnet
"""

import copy
import json
import re
from typing import Any, Type, TypeVar

import litellm
from litellm import Router
from pydantic import BaseModel
from typing_extensions import override

from lec02_01_litellm.config import llm_config

T = TypeVar("T", bound=BaseModel)

STREAMING_RETRY_COUNT = 3
NON_STREAMING_RETRY_COUNT = 3
STREAMING_REQUEST_TIMEOUT = 600


class CustomRouter(Router):
    """스트리밍 재시도/fallback 및 response_model 파싱을 지원하는 확장 Router."""

    # ── acompletion 오버라이드 ────────────────────────────────────

    @override
    async def acompletion(self, *args, **kwargs):
        """Non-streaming / streaming 모두 지원하는 acompletion.

        stream=True 인 경우 _acompletion_streaming으로 위임하여
        재시도 + fallback + first-chunk 검증을 수행합니다.
        """
        if kwargs.get("stream"):
            return await self._acompletion_streaming(*args, **kwargs)

        return await super().acompletion(*args, **kwargs)

    async def _acompletion_streaming(self, **kwargs) -> litellm.CustomStreamWrapper:
        """재시도 및 fallback을 지원하는 스트리밍 completion.

        1. 설정된 재시도 횟수만큼 시도
        2. 실패 시 fallback 모델로 전환
        3. 첫 유효 청크를 검증하여 스트림 정상 여부 확인
        4. CustomStreamWrapper로 감싸서 반환
        """
        model: str = kwargs.pop("model", "claude-4.5-sonnet")
        num_retries: int = kwargs.pop("num_retries", STREAMING_RETRY_COUNT)

        default_stream_options: dict[str, Any] = {"include_usage": True}
        user_stream_options: dict[str, Any] = kwargs.pop("stream_options", {})
        stream_options: dict[str, Any] = {**default_stream_options, **user_stream_options}

        kwargs.pop("stream", None)  # super().acompletion에서 중복 방지

        default_fallbacks = self._prepare_fallbacks(model)
        for _ in range(num_retries + 1):
            try:
                current_kwargs = copy.deepcopy(kwargs)

                response = await super().acompletion(
                    model=model,
                    stream=True,
                    stream_options=stream_options,
                    num_retries=0,
                    timeout=STREAMING_REQUEST_TIMEOUT,
                    **current_kwargs,
                )

                # 첫 유효 청크 검증 — 빈 스트림 조기 감지
                original_generator = response.completion_stream
                first_chunk = await self._validate_first_chunk(original_generator)
                new_generator = self._wrapper_generator(first_chunk, original_generator)

                return litellm.CustomStreamWrapper(
                    completion_stream=new_generator,
                    model=response.model,
                    custom_llm_provider=response.custom_llm_provider,
                    logging_obj=response.logging_obj,
                )
            except Exception:
                model = default_fallbacks.pop(0) if default_fallbacks else "claude-4.5-sonnet"

        raise Exception(f"Failed to get streaming response for {model}")

    def _prepare_fallbacks(self, model: str) -> list[str]:
        """스트리밍 재시도에 사용할 fallback 모델 목록을 준비합니다."""
        default_fallbacks = (
            self._get_fallbacks(self.fallbacks, model) if self.fallbacks else [model]
        )
        # fallback 수가 재시도 횟수보다 적으면 반복하여 채움
        if len(default_fallbacks) < STREAMING_RETRY_COUNT:
            default_fallbacks.append(model)
            default_fallbacks = default_fallbacks * (
                STREAMING_RETRY_COUNT // len(default_fallbacks) + 1
            )
        return default_fallbacks

    # ── fallback 헬퍼 ──────────────────────────────────────────────

    @staticmethod
    def _get_fallbacks(fallback_list: list[dict], model: str) -> list[str]:
        """fallback 설정에서 해당 모델의 fallback 목록을 가져옵니다."""
        for fallback in fallback_list:
            fallback_models = fallback.get(model)
            if fallback_models is not None:
                return fallback_models.copy()
        return []

    # ── 스트리밍 first-chunk 검증 ─────────────────────────────────

    @staticmethod
    async def _validate_first_chunk(generator: Any) -> Any:
        """스트림의 첫 유효 청크를 찾아 반환합니다.

        빈 청크를 건너뛰고, 실제 content/reasoning이 있는 첫 청크를 반환합니다.
        스트림이 유효한 청크 없이 종료되면 예외를 발생시킵니다.
        """
        async for chunk in generator:
            if chunk and chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                if any(
                    [
                        getattr(delta, "content", None),
                        getattr(delta, "reasoning_content", None),
                        getattr(delta, "thinking_blocks", None),
                    ]
                ):
                    return chunk

        raise Exception("Stream ended without a valid chunk")

    @staticmethod
    async def _wrapper_generator(first_chunk: Any, original_generator: Any):
        """검증된 첫 청크를 먼저 yield하고 나머지 스트림을 이어서 yield합니다."""
        yield first_chunk
        async for chunk in original_generator:
            yield chunk

    # ── response_model 파싱 ───────────────────────────────────────

    async def acompletion_with_response_model(self, response_model: Type[T], **kwargs) -> T:
        """Pydantic 모델로 구조화된 응답을 반환하는 acompletion 래퍼.

        response_format에 Pydantic 모델을 전달하여 LLM이 해당 스키마에 맞는
        JSON을 생성하도록 유도하고, 자동으로 파싱하여 모델 인스턴스를 반환합니다.

        Args:
            response_model: 응답을 파싱할 Pydantic 모델 클래스
            **kwargs: acompletion에 전달할 추가 인자

        Returns:
            파싱된 Pydantic 모델 인스턴스

        Raises:
            Exception: 재시도 후에도 파싱에 실패한 경우
        """
        num_retries = kwargs.pop("num_retries", NON_STREAMING_RETRY_COUNT)
        for _ in range(num_retries + 1):
            try:
                response = await self.acompletion(
                    response_format=response_model,
                    num_retries=0,
                    **kwargs,
                )
                content = response.choices[0].message.content  # type: ignore
                if content.strip().startswith("```json"):
                    json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1)
                return response_model(**json.loads(content))
            except Exception:
                continue

        raise Exception(f"Failed to get {response_model.__name__} response")


def init_router() -> CustomRouter:
    """LiteLLM Router를 초기화합니다.

    Returns:
        Router: 설정된 LiteLLM Router 인스턴스
    """
    # model_name vs litellm_params.model 차이점:
    #
    # - model_name: Router에서 사용하는 별칭 (alias)
    #   → acompletion(model="gpt-5", ...) 호출 시 이 이름을 사용
    #   → fallback 설정에서도 이 이름을 참조
    #   → 사용자가 기억하기 쉬운 간단한 이름으로 정의
    #
    # - litellm_params.model: 실제 프로바이더 API에 전달되는 모델 식별자
    #   → OpenAI: "gpt-5", "gpt-5-mini" (API 공식 모델명)
    #   → Anthropic: "claude-sonnet-4-5-20250929" (버전 날짜 포함)
    #   → Google: "gemini/gemini-3-flash-preview" (프로바이더 prefix 필요)
    #
    # 이 분리를 통해:
    # 1. 모델 버전 업데이트 시 model_name은 유지하고 litellm_params.model만 변경 가능
    # 2. 동일 모델을 다른 API 키로 여러 번 등록 가능 (로드밸런싱)
    # 3. 프로바이더별 명명 규칙 차이를 추상화
    model_list = [
        {
            "model_name": "gpt-5",  # Router 호출 시 사용하는 별칭
            "litellm_params": {
                "model": "gpt-5",  # OpenAI API에 전달되는 실제 모델명
                "api_key": llm_config.openai_api_key,
            },
        },
        {
            "model_name": "gpt-5-mini",
            "litellm_params": {
                "model": "gpt-5-mini",
                "api_key": llm_config.openai_api_key,
            },
        },
        {
            "model_name": "claude-4.5-sonnet",
            "litellm_params": {
                "model": "claude-sonnet-4-5-20250929",  # Anthropic API 형식 (버전 날짜 포함)
                "api_key": llm_config.anthropic_api_key,
            },
        },
        {
            "model_name": "claude-4.5-haiku",
            "litellm_params": {
                "model": "claude-haiku-4-5-20251001",
                "api_key": llm_config.anthropic_api_key,
            },
        },
        {
            "model_name": "claude-4.5-opus",
            "litellm_params": {
                "model": "anthropic/claude-opus-4-5-20251101",
                "api_key": llm_config.anthropic_api_key,
            },
        },
        {
            "model_name": "gemini-3-flash",
            "litellm_params": {
                "model": "gemini/gemini-3-flash-preview",  # Google AI Studio 형식 (gemini/ prefix)
                "api_key": llm_config.google_api_key,
            },
        },
        {
            "model_name": "gemini-3-pro",
            "litellm_params": {
                "model": "gemini/gemini-3-pro-preview",
                "api_key": llm_config.google_api_key,
            },
        },
        {
            "model_name": "gpt-4.1-mini",
            "litellm_params": {
                "model": "gpt-4.1-mini",
                "api_key": llm_config.openai_api_key,
            },
        },
    ]

    fallbacks = [
        {"gpt-5": ["claude-4.5-sonnet", "gemini-3-flash"]},
        {"gpt-5-mini": ["gemini-3-flash", "gpt-5"]},
        {"claude-4.5-sonnet": ["gpt-5", "gemini-3-flash"]},
        {"claude-4.5-haiku": ["claude-4.5-sonnet", "gemini-3-flash"]},
        {"claude-4.5-opus": ["claude-4.5-sonnet", "gpt-5"]},
        {"gemini-3-flash": ["gpt-5", "claude-4.5-sonnet"]},
        {"gemini-3-pro": ["gpt-5", "claude-4.5-sonnet", "claude-4.5-opus"]},
        {"gpt-4.1-mini": ["gpt-5-mini", "gemini-3-flash"]},
    ]

    context_window_fallbacks = [
        {"gpt-5": ["gemini-3-flash"]},
        {"claude-4.5-sonnet": ["gemini-3-flash"]},
        {"claude-4.5-haiku": ["gemini-3-flash"]},
        {"claude-4.5-opus": ["gemini-3-flash"]},
        {"gemini-3-flash": ["gpt-5"]},
        {"gemini-3-pro": ["gpt-5"]},
        {"gpt-4.1-mini": ["gpt-5-mini"]},
    ]

    return CustomRouter(
        model_list=model_list,
        routing_strategy="simple-shuffle",
        allowed_fails=3,
        cooldown_time=10,
        max_fallbacks=2,
        fallbacks=fallbacks,
        context_window_fallbacks=context_window_fallbacks,
    )


router = init_router()
