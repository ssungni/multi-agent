"""환경 변수 설정 모듈.

.env 파일에서 환경 변수를 로딩하여 LLM API 키를 제공합니다.

Usage Example:
    from lec02_01_litellm.config import llm_config

    # router.py에서 사용
    router = Router(
        model_list=[
            {
                "model_name": "gpt-4",
                "litellm_params": {"api_key": llm_config.openai_api_key, ...}
            },
            {
                "model_name": "claude",
                "litellm_params": {"api_key": llm_config.anthropic_api_key, ...}
            },
        ]
    )
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# .env 파일 로딩 (lecture/ 디렉토리 기준)
_lecture_dir = Path(__file__).parent.parent
load_dotenv(_lecture_dir / ".env")


@dataclass(frozen=True)
class LLMConfig:
    """LLM API 설정."""

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")


# 싱글톤 인스턴스
llm_config = LLMConfig()
