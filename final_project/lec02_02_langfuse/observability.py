"""Langfuse 모니터링 설정 모듈.

Langfuse를 활용한 LLM 호출 모니터링 및 트레이싱을 설정합니다.

Basic Usage Example:
    from lec02_02_langfuse.observability import setup_langfuse, observe, langfuse_context

    # 1. Langfuse 초기화 (애플리케이션 시작 시 한 번만)
    setup_langfuse()

    # 2. @observe 데코레이터로 함수 트레이싱
    @observe(capture_input=True, capture_output=True)
    async def generate_response(prompt: str) -> str:
        # langfuse_context로 trace 메타데이터 추가
        langfuse_context.update_current_trace(
            user_id="user_123",
            session_id="session_abc",
            metadata={"model": "gpt-4"},
        )
        response = await llm_call(prompt)
        return response

    # 3. 중첩된 함수 호출도 자동으로 트레이싱됨
    @observe(capture_input=True, capture_output=True)
    async def process_request(user_input: str) -> str:
        # 이 함수의 호출이 상위 trace의 하위 span으로 기록됨
        result = await generate_response(user_input)
        return result

Advanced langfuse_context Usage Examples:

    Example 1: Trace-level metadata (전체 요청에 대한 메타데이터)
        @observe(capture_input=True, capture_output=True)
        async def run_agent(user_id: str, query: str) -> str:
            # update_current_trace()는 최상위 trace에 메타데이터를 추가
            # 모든 하위 span에서 이 정보를 공유할 수 있음
            langfuse_context.update_current_trace(
                user_id=user_id,  # 사용자 식별
                session_id=f"session_{user_id}_20260123",  # 세션 추적
                tags=["production", "agent", "v2"],  # 태그로 필터링 가능
                metadata={
                    "environment": "prod",
                    "agent_version": "2.0.1",
                    "query_length": len(query),
                },
            )
            result = await agent.execute(query)
            return result

    Example 2: Observation-level metadata (개별 span에 대한 메타데이터)
        @observe(capture_input=True, capture_output=True)
        async def call_llm(prompt: str, model: str) -> str:
            # update_current_observation()은 현재 함수 호출(span)에만 메타데이터 추가
            # 특정 단계의 상세 정보를 기록할 때 유용
            langfuse_context.update_current_observation(
                name="llm_generation",  # span 이름 커스터마이징
                metadata={
                    "model": model,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "prompt_length": len(prompt),
                },
            )
            response = await llm.generate(prompt, model=model)
            return response

    Example 3: Multi-agent conversation tracking
        class ChatAgent:
            @observe(capture_input=True, capture_output=True)
            async def run(self, user_id: str, message: str) -> str:
                # trace 레벨: 전체 대화 세션 정보
                langfuse_context.update_current_trace(
                    user_id=user_id,
                    session_id=self.session_id,
                    tags=["chat", "multi-turn"],
                    metadata={
                        "conversation_turn": self.turn_count,
                        "total_messages": len(self.history),
                    },
                )

                # observation 레벨: 현재 turn의 상세 정보
                langfuse_context.update_current_observation(
                    name=f"turn_{self.turn_count}",
                    metadata={
                        "message_length": len(message),
                        "has_tools": bool(self.available_tools),
                    },
                )

                response = await self._generate_response(message)
                self.turn_count += 1
                return response

            @observe(capture_input=True, capture_output=True)
            async def _generate_response(self, message: str) -> str:
                # 중첩된 함수에서도 langfuse_context 사용 가능
                # 이 observation은 run()의 하위 span이 됨
                langfuse_context.update_current_observation(
                    metadata={
                        "step": "response_generation",
                        "context_size": len(self.history),
                    },
                )
                return await self.llm.generate(message)

    Example 4: Error tracking and debugging
        @observe(capture_input=True, capture_output=True)
        async def process_with_retry(prompt: str, max_retries: int = 3) -> str:
            langfuse_context.update_current_trace(
                metadata={"max_retries": max_retries},
            )

            for attempt in range(max_retries):
                try:
                    langfuse_context.update_current_observation(
                        metadata={
                            "attempt": attempt + 1,
                            "status": "attempting",
                        },
                    )
                    result = await llm_call(prompt)

                    # 성공 시 메타데이터 업데이트
                    langfuse_context.update_current_observation(
                        metadata={
                            "attempt": attempt + 1,
                            "status": "success",
                            "final_attempt": attempt + 1,
                        },
                    )
                    return result

                except Exception as e:
                    # 실패 시 에러 정보 기록
                    langfuse_context.update_current_observation(
                        metadata={
                            "attempt": attempt + 1,
                            "status": "failed",
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )
                    if attempt == max_retries - 1:
                        raise

            return ""

    Example 5: Tool usage tracking in agents
        @observe(capture_input=True, capture_output=True)
        async def execute_tool(tool_name: str, arguments: dict) -> dict:
            # tool 실행 전 메타데이터 설정
            langfuse_context.update_current_observation(
                name=f"tool_{tool_name}",
                metadata={
                    "tool_name": tool_name,
                    "argument_count": len(arguments),
                    "arguments": arguments,  # 인자 전체 기록
                },
            )

            result = await tools[tool_name].execute(**arguments)

            # tool 실행 후 결과 메타데이터 추가
            langfuse_context.update_current_observation(
                metadata={
                    "result_size": len(str(result)),
                    "execution_status": "success",
                },
            )

            return result

Key Concepts:
    - update_current_trace(): 전체 요청 레벨의 메타데이터 (user_id, session_id, tags 등)
    - update_current_observation(): 현재 함수 호출(span) 레벨의 메타데이터
    - 중첩 호출: 자동으로 부모-자식 관계가 형성되어 트리 구조로 시각화됨
    - tags: Langfuse UI에서 필터링 및 그룹핑에 활용
    - metadata: 커스텀 데이터 기록 (분석 및 디버깅용)
"""

from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe

from lec02_02_langfuse.config import langfuse_config

# Re-export decorators for convenient import
__all__ = ["setup_langfuse", "observe", "langfuse_context"]


def setup_langfuse() -> Langfuse:
    """Langfuse 클라이언트를 초기화합니다.

    환경 변수를 통해 Langfuse 설정을 로드하고 클라이언트를 생성합니다.
    이 함수는 애플리케이션 시작 시 한 번만 호출하면 됩니다.

    환경 변수 (.env 파일):
        LANGFUSE_PUBLIC_KEY: Langfuse 프로젝트의 Public Key
        LANGFUSE_SECRET_KEY: Langfuse 프로젝트의 Secret Key
        LANGFUSE_HOST: Langfuse 서버 URL (기본값: https://cloud.langfuse.com)

    Returns:
        Langfuse: 초기화된 Langfuse 클라이언트 인스턴스

    Example:
        # app.py
        from lec02_02_langfuse.observability import setup_langfuse

        # 애플리케이션 시작 시 초기화
        langfuse_client = setup_langfuse()

        # 이후 @observe 데코레이터가 자동으로 이 클라이언트를 사용함
        @observe(capture_input=True, capture_output=True)
        async def main():
            ...

    Note:
        - 환경 변수가 설정되지 않으면 빈 문자열로 초기화됩니다
        - @observe 데코레이터는 전역 Langfuse 설정을 자동으로 사용합니다
        - LiteLLM과 함께 사용할 경우 litellm.success_callback = ["langfuse"]로 설정
    """
    return Langfuse(
        public_key=langfuse_config.public_key,
        secret_key=langfuse_config.secret_key,
        host=langfuse_config.host,
    )
