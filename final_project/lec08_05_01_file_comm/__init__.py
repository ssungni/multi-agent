"""파일 기반 커뮤니케이션 시스템 (강의 08-05-01)

Sub-agent 출력을 로컬 파일로 저장하고, 파일 경로만 전달하여
컨텍스트 윈도우를 절약하는 패턴을 구현합니다.

주요 구성요소:
- workspace.py: WorkspaceManager - 파일 I/O 관리
- tools.py: 파일 기반 도구들 + ReadFileTool
- prompts.py: 파일 기반 워크플로우 시스템 프롬프트
- agent.py: FileCommOrchestratorAgent
- main.py: 통합 실행 데모
"""
