"""파일 기반 커뮤니케이션 시스템 프롬프트.

기존 ORCHESTRATOR_SYSTEM_PROMPT를 확장하여
파일 기반 워크플로우 가이드라인을 추가합니다.
"""

from lec06_01_orchestrator.prompts import ORCHESTRATOR_SYSTEM_PROMPT

FILE_COMM_SYSTEM_PROMPT = (
    ORCHESTRATOR_SYSTEM_PROMPT
    + """

## File-Based Communication

Sub-agent results are saved as files. Tool responses contain file paths, not full content.
- Use `read_file` tool to inspect contents when needed
- Only read files when you need to verify or reference specific details
- Available files: outline.json, research.json, report.json

This approach saves context window space by keeping large results on disk
and only loading them into context when explicitly needed."""
)
