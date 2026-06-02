"""환경 변수 설정 모듈.

.env 파일에서 환경 변수를 로딩하여 Langfuse 설정을 제공합니다.

Usage Example:
    from lec02_02_langfuse.config import langfuse_config

    langfuse_client = Langfuse(
        public_key=langfuse_config.public_key,
        secret_key=langfuse_config.secret_key,
        host=langfuse_config.host,
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
class LangfuseConfig:
    """Langfuse 모니터링 설정."""

    public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    host: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")


# 싱글톤 인스턴스
langfuse_config = LangfuseConfig()
