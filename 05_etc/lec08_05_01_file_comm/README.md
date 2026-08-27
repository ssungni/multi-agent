# lec08_05_01_file_comm — File-based Communication

> Sub-agent 출력을 로컬 파일로 저장하고, 파일 경로만 전달하여 컨텍스트 윈도우를 절약합니다.

## 개요

Multi-agent 시스템에서 Sub-agent의 출력(아웃라인, 리서치, 리포트)은 수천~수만 토큰에 달할 수 있습니다.
이 모든 내용을 Orchestrator의 컨텍스트 윈도우에 넣으면 토큰 비용이 급증하고, 윈도우 한계에 도달할 수 있습니다.

**File-based Communication**은 이 문제를 해결합니다:
1. Sub-agent 결과를 JSON 파일로 저장
2. LLM에는 요약 + 파일 경로만 전달
3. LLM이 상세 내용이 필요하면 `read_file` 도구로 조회

## 핵심 개념

### Before (기존 방식)
```
Tool Result → LLM Context (전체 내용, 5,000+ tokens)
"Outline generated: 'AI Trends'
Sections:
  1. Intro: AI의 역사와 현재...
  2. Market: 시장 규모 분석...
  ..."
```

### After (파일 기반 방식)
```
Tool Result → LLM Context (요약 + 경로, ~50 tokens)
"Outline generated: 'AI Trends' (5 sections).
Saved to: /path/outline.json
Use read_file to inspect details."
```

## 아키텍처

```
FileCommOrchestratorAgent
├── extends OptimizedOrchestratorAgent (lec08_04)
│     ├── ModelSelector (작업별 모델 선택)
│     └── Cache Control (3-block strategy)
│
├── WorkspaceManager
│     └── workspace_{uuid}/ 디렉터리에 파일 저장
│
├── FileComm Tools (기존 도구 상속)
│     ├── FileCommCallOutlinerTool → outline.json
│     ├── FileCommCallResearcherTool → research.json
│     └── FileCommCallWriterTool → report.json
│
├── ReadFileTool (신규)
│     └── 워크스페이스 파일을 읽어 LLM에 반환
│
└── FinalAnswerTool (기존 재사용)
```

## 파일 구조

```
lec08_05_01_file_comm/
├── __init__.py       # 패키지 초기화
├── workspace.py      # WorkspaceManager: 파일 I/O 관리
├── tools.py          # 파일 기반 도구들 + ReadFileTool
├── prompts.py        # 파일 기반 워크플로우 시스템 프롬프트
├── agent.py          # FileCommOrchestratorAgent
├── main.py           # 통합 실행 데모
└── README.md         # 이 문서
```

## 코드 읽기 순서

1. **workspace.py** - WorkspaceManager의 파일 I/O 인터페이스
2. **prompts.py** - 파일 기반 시스템 프롬프트 확장
3. **tools.py** - 기존 도구 상속 + ReadFileTool
4. **agent.py** - FileCommOrchestratorAgent 통합
5. **main.py** - 데모 실행 흐름 및 토큰 절약 비교

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec08-05-01
```

## 학습 포인트

### 1. 파일 기반 커뮤니케이션 패턴
도구 결과를 파일로 저장하고 경로만 전달하면:
- 컨텍스트 윈도우 사용량 대폭 감소
- LLM이 "필요할 때만" 상세 내용 조회 (lazy loading)
- 대규모 결과일수록 절약 효과가 큼

### 2. 상속을 통한 점진적 확장
```python
OrchestratorAgent           # 기본 오케스트레이션
└── OptimizedOrchestratorAgent  # + 비용 최적화
    └── FileCommOrchestratorAgent  # + 파일 기반 커뮤니케이션
```

### 3. ReadFileTool의 역할
LLM이 `read_file`을 호출하는 것은 "context window에 데이터를 로드"하는 것과 같습니다.
필요할 때만 호출하므로, 불필요한 데이터가 컨텍스트를 차지하지 않습니다.

## 참고 자료

- **OptimizedOrchestratorAgent**: `lecture/lec08_04_cost/main.py`
- **CallOutlinerTool 등**: `lecture/lec06_01_orchestrator/tools.py`
- **ORCHESTRATOR_SYSTEM_PROMPT**: `lecture/lec06_01_orchestrator/prompts.py`

---

## 강의 네비게이션

← [이전 강의: lec08_04_cost - 비용/속도 최적화](../lec08_04_cost/README.md) | [다음 강의: lec08_05_02_context - Context Engineering](../lec08_05_02_context/README.md) →
