"""Langfuse 콜백이 통합된 LiteLLM Router.

lec02_01의 Router를 가져와서 Langfuse 콜백을 등록합니다.
이 모듈을 import하면 자동으로 Langfuse 콜백이 설정됩니다.

Usage Example:
    from lec02_02_langfuse.router import router

    response = await router.acompletion(
        model="claude-4.5-sonnet",
        messages=[{"role": "user", "content": "Hello!"}]
    )
"""

import litellm

from lec02_01_litellm.router import router

# LiteLLM에 Langfuse 콜백 등록
# 모든 LLM 호출(성공/실패)을 Langfuse에 자동으로 전송하여 트레이싱 및 모니터링합니다.
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

__all__ = ["router"]
