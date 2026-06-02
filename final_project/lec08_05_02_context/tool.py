"""컨텍스트 압축 기능이 포함된 도구 인터페이스.

확장 원본: lec06_02_hitl/tool.py

이 모듈은 도구 결과를 압축하는 기능을 개선하여 컨텍스트 크기를 줄입니다.
주요 개선사항:
- compact_result() 메서드가 URL을 추출하고 보존합니다.
- 압축된 결과에서 재검색을 위한 가이던스를 제공합니다.
- 결과 개수와 주요 URL을 포함하여 압축 효율성을 높입니다.
"""

from typing import Any

from lec06_02_hitl.tool import (
    BaseTool as BaseTool_lec06,
)
from lec06_02_hitl.tool import (
    ToolResult,
)
from lec08_05_02_context.cache_control import COMPACTION_START_MARKER

# Re-export for compatibility
__all__ = ["BaseTool", "ToolResult", "COMPACTION_START_MARKER"]


class BaseTool(BaseTool_lec06):
    """컨텍스트 압축 기능이 개선된 도구 기본 클래스.

    lec06_02_hitl의 BaseTool을 확장하여 compact_result() 메서드를 개선합니다.
    압축 시 URL을 추출하고 보존하여, 필요 시 재검색할 수 있도록 합니다.
    """

    # [ADDED in lec08_05_context]
    def compact_result(self, arguments: dict[str, Any], content: str) -> str:
        """컨텍스트 관리를 위해 도구 결과를 압축하고 URL을 보존합니다.

        이 개선된 구현은 다음을 수행합니다:
        1. 콘텐츠에서 URL 패턴을 추출
        2. 추출된 URL 목록과 결과 개수를 포함한 압축 메시지 생성
        3. 재검색을 위한 가이던스 제공

        서브클래스는 도구별 URL 추출 로직을 구현하기 위해 이 메서드를
        오버라이드할 수 있습니다.

        Args:
            arguments: 도구에 전달된 인자
            content: 도구 결과의 원본 콘텐츠

        Returns:
            압축된 콘텐츠 문자열. URL이 발견되면 목록과 함께 반환하고,
            그렇지 않으면 일반 압축 메시지를 반환합니다.
        """
        _ = arguments

        # URL 추출 (http:// 또는 https://로 시작하는 URL)
        urls = []
        for line in content.split("\n"):
            if "URL:" in line or "http" in line:
                parts = line.split()
                for part in parts:
                    if part.startswith("http"):
                        # 뒤따르는 구두점 제거
                        url = part.rstrip(",.)")
                        urls.append(url)

        # URL이 발견되면 구조화된 압축 메시지 생성
        if urls:
            # 중복 제거 및 최대 10개까지만 표시
            unique_urls = list(dict.fromkeys(urls))
            url_list = ", ".join([f"[{i + 1}] {url}" for i, url in enumerate(unique_urls[:10])])
            suffix = "..." if len(unique_urls) > 10 else ""
            url_info = f"{len(unique_urls)} URLs: {url_list}{suffix}"
            return (
                f"{COMPACTION_START_MARKER} {self.name} result. "
                f"{url_info}. "
                f"Content omitted for space. Re-run {self.name} if full content needed."
            )

        # URL이 없으면 기본 압축 메시지 반환
        return f"{COMPACTION_START_MARKER} {self.name} result. Content omitted for space."
