# LLM Agent 개발 강의

> Report Generation Agent를 중심 예제로, LLM Router부터 Context Engineering까지 점진적으로 학습합니다.

LLM Agent 개발에 필요한 핵심 개념과 구현 방법을 다루는 실습 코드입니다.

## 강의 로드맵 / Learning Path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            LLM Agent 개발 강의 흐름                            │
└─────────────────────────────────────────────────────────────────────────────┘

[CH02] Foundation - LLM 호출 인프라
    │
    ├─ lec02_01: LiteLLM (Multi-Provider Router + Fallback)
    ├─ lec02_02: Langfuse (Observability & Tracing)
    ├─ lec02_03: vLLM (On-Premise LLM Serving) ※참고용
    └─ lec02_04: Streamlit (Chat UI)
    │
    ▼

[CH04] Agent Basics - Agentic Loop & Tools
    │
    ├─ lec04_01: BaseAgent (Think → Act → Observe Loop)
    └─ lec04_02: Common Tools (SearchTool, FetchTool)
    │
    ▼

[CH05] Sub-Agents - 도메인별 Agent 구현
    │
    ├─ lec05_01: OutlinerAgent (아웃라인 생성 + Evaluator 피드백)
    ├─ lec05_02: ResearcherAgent (섹션별 리서치 + Orchestrator-SubAgent 패턴)
    └─ lec05_03: WriterAgent (리포트 작성 + Section/Report 레벨 평가)
    │
    ▼

[CH06] Orchestration - Multi-Agent 조율
    │
    ├─ lec06_01: OrchestratorAgent (Sub-agent 워크플로우 관리)
    └─ lec06_02: HITL (Human-In-The-Loop 통합)
    │
    ▼

[CH07] Tools - 고급 도구 시스템
    │
    └─ lec07_02: AskUserQuestion (HITL 기반 사용자 질문 도구)
    │
    ▼

[CH08] Optimization - 성능 최적화
    │
    ├─ lec08_03: Quality (프롬프트 엔지니어링)
    ├─ lec08_04: Cost/Speed (Cache Control, 모델 전환, 비용 최적화)
    ├─ lec08_05_01: File-based Communication (파일 기반 컨텍스트 절약)
    └─ lec08_05_02: Context Engineering (2단계 컨텍스트 압축)
```

## 강의 구성

| 강의 | 주제 | 설명 |
|------|------|------|
| lec02_01_litellm | LiteLLM | 멀티 프로바이더 LLM 호출 및 Fallback |
| lec02_02_langfuse | Langfuse | Observability 및 추적 |
| lec02_03_vllm | vLLM | 폐쇄망 오픈소스 LLM 서빙 (README만) |
| lec02_04_streamlit | Streamlit | LiteLLM 기반 채팅 UI |
| lec04_01_base_agent | BaseAgent | 기본 Agentic Loop 구현 |
| lec04_02_tools | Common Tools | SearchTool, FetchTool (웹 검색/추출) |
| lec05_01_outliner | OutlinerAgent | 아웃라인 생성 + Evaluator 피드백 루프 |
| lec05_02_researcher | ResearcherAgent | 섹션별 리서치 + Orchestrator-SubAgent 패턴 |
| lec05_03_writer | WriterAgent | 리포트 작성 + Section/Report 레벨 평가 |
| lec06_01_orchestrator | OrchestratorAgent | Sub-agent 조율 및 워크플로우 관리 |
| lec06_02_hitl | Human-In-The-Loop | HITL 메커니즘 및 Orchestrator 통합 |
| lec07_02_ask_user | AskUserQuestion | HITL 기반 사용자 질문 도구 |
| lec08_03_quality | 퀄리티 개선 | 프롬프트 엔지니어링 전략 (코드 모듈, 실행 없음) |
| lec08_04_cost | 비용/속도 최적화 | Cache Control, 모델 전환, 비용 최적화 |
| lec08_05_01_file_comm | File-based Communication | 파일 기반 커뮤니케이션으로 컨텍스트 윈도우 절약 |
| lec08_05_02_context | Context Engineering | 2단계 컨텍스트 압축 전략 (Compaction + Summarization) |

## 디렉토리 구조

```
lecture/
├── README.md
├── pyproject.toml
├── .env.example
├── archiecture/                       # Architecture 문서
│   ├── orchestrator.md
│   ├── outliner_agent.md
│   ├── researcher_agent.md
│   └── writer_agent.md
│
├── lec02_01_litellm/                  # CH02_01: LiteLLM Multi-Provider
│   ├── config.py
│   ├── router.py
│   └── main.py
│
├── lec02_02_langfuse/                 # CH02_02: Langfuse Observability
│   ├── config.py
│   ├── observability.py
│   ├── router.py
│   └── main.py
│
├── lec02_03_vllm/                     # CH02_03: vLLM (README만)
│   └── README.md
│
├── lec02_04_streamlit/                # CH02_04: Streamlit Chat UI
│   ├── app.py
│   └── main.py
│
├── lec04_01_base_agent/               # CH04_01: BaseAgent (Agentic Loop)
│   ├── base.py
│   ├── state.py
│   ├── tool.py
│   ├── constant.py
│   ├── example_agent.py
│   └── main.py
│
├── lec04_02_tools/                    # CH04_02: Common Tools
│   ├── schemas.py
│   ├── search.py
│   ├── fetch.py
│   └── main.py
│
├── lec05_01_outliner/                 # CH05_01: Outliner Agent
│   ├── schemas.py
│   ├── state.py
│   ├── prompts.py
│   ├── tools.py
│   ├── evaluator.py
│   ├── agent.py
│   └── main.py
│
├── lec05_02_researcher/               # CH05_02: Researcher Agent
│   ├── schemas.py
│   ├── state.py
│   ├── search_agent_state.py
│   ├── prompts.py
│   ├── tools.py
│   ├── search_agent_tools.py
│   ├── evaluator.py
│   ├── agent.py
│   ├── search_agent.py
│   └── main.py
│
├── lec05_03_writer/                   # CH05_03: Writer Agent
│   ├── schemas.py
│   ├── state.py
│   ├── prompts.py
│   ├── tools.py
│   ├── evaluator.py
│   ├── agent.py
│   └── main.py
│
├── lec06_01_orchestrator/             # CH06_01: Orchestrator Agent
│   ├── state.py
│   ├── prompts.py
│   ├── tools.py
│   ├── agent.py
│   └── main.py
│
├── lec06_02_hitl/                     # CH06_02: HITL
│   ├── base.py
│   ├── state.py
│   ├── tool.py
│   ├── hitl.py
│   ├── ask_outline_approval.py
│   ├── agent.py
│   └── main.py
│
├── lec07_02_ask_user/                 # CH07_02: AskUserQuestion
│   ├── base.py
│   ├── state.py
│   ├── hitl.py
│   ├── ask_user.py
│   └── main.py
│
├── lec08_03_quality/                  # CH08_03: 퀄리티 개선
│   ├── prompts.py
│   └── evaluator.py
│
├── lec08_04_cost/                     # CH08_04: 비용/속도 최적화
│   ├── base.py
│   ├── cache_control.py
│   ├── evaluators.py
│   ├── model_selector.py
│   ├── search.py
│   └── main.py
│
├── lec08_05_01_file_comm/             # CH08_05_01: File-based Communication
│   ├── agent.py
│   ├── prompts.py
│   ├── tools.py
│   ├── workspace.py
│   └── main.py
│
└── lec08_05_02_context/               # CH08_05_02: Context Engineering
    ├── manager.py
    ├── compaction.py
    ├── summarization.py
    ├── cache_control.py
    ├── calculate_size.py
    ├── tool.py
    ├── base.py
    └── main.py
```

## 개발 환경 셋업

### 1. Rye 설치

```bash
# macOS/Linux
curl -sSf https://rye.astral.sh/get | bash

# 또는 Homebrew
brew install rye
```

### 2. 의존성 설치

```bash
cd lecture
rye sync
```

### 3. 환경 변수 설정

`.env.example`을 참고하여 `.env` 파일을 생성합니다:

```bash
cp .env.example .env
```

`.env` 파일에 API 키를 설정합니다:

```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# External Service API Keys
SERPER_API_KEY=...  # https://serper.dev (웹 검색 기능에 필요)
```

### 4. VS Code 설정 (권장)

```json
{
  "mypy-type-checker.path": ["${workspaceFolder}/.venv/bin/mypy"],
  "mypy-type-checker.args": ["--check-untyped-defs"],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "always",
      "source.fixAll": "explicit"
    }
  }
}
```

## API 키 발급

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys
- **Google AI**: https://aistudio.google.com/app/apikey
- **Langfuse**: https://cloud.langfuse.com (회원가입 후 프로젝트 생성)
- **Serper**: https://serper.dev (웹 검색 API)

## 강의 실행

각 강의는 독립적으로 실행할 수 있습니다:

```bash
# Foundation (CH02)
rye run lec02-01          # LiteLLM 멀티 프로바이더 호출
rye run lec02-02          # Langfuse Observability
rye run lec02-04          # Streamlit 채팅 UI

# Agent Basics (CH04)
rye run lec04-01          # BaseAgent Agentic Loop
rye run lec04-02          # Common Tools (SearchTool, FetchTool)

# Sub-Agents (CH05)
rye run lec05-01          # OutlinerAgent (아웃라인 생성)
rye run lec05-02          # ResearcherAgent (섹션별 리서치)
rye run lec05-03          # WriterAgent (리포트 작성)

# Orchestrator & HITL (CH06)
rye run lec06-01          # OrchestratorAgent (워크플로우 조율)
rye run lec06-02          # HITL 통합 Orchestrator

# Tools (CH07)
rye run lec07-02          # AskUserQuestion HITL 도구

# Optimization (CH08)
# lec08-03은 코드 모듈만 제공 (실행 데모 없음)
rye run lec08-04          # 비용/속도 최적화 (Baseline vs Optimized)
rye run lec08-05-01       # File-based Communication (파일 기반 컨텍스트 절약)
rye run lec08-05-02       # Context Engineering (2단계 컨텍스트 압축)
```

또는 직접 모듈을 실행할 수 있습니다:

```bash
rye run python -m lec05_01_outliner.main
```

## Architecture 문서

Report Generation Agent의 상세 아키텍처는 다음 문서를 참고하세요:

| 문서 | 설명 |
|------|------|
| `archiecture/orchestrator.md` | Orchestrator Agent 워크플로우, HITL 통합, Sub-agent 조율 |
| `archiecture/outliner_agent.md` | Outliner Agent 피드백 루프, Query Expansion, 평가 전략 |
| `archiecture/researcher_agent.md` | Researcher Agent 병렬 파이프라인, Required Info 평가 |
| `archiecture/writer_agent.md` | Writer Agent 섹션별 작성, Section/Report 레벨 평가 |

## 개발 도구

- **[rye](https://rye.astral.sh/)**: 프로젝트 및 패키지 관리
- **[ruff](https://docs.astral.sh/ruff/)**: 자동 포맷터 + 린터
- **[mypy](https://mypy.readthedocs.io/)**: 타입 체커

```bash
# 린팅
ruff check .

# 타입 체크
mypy .

# 테스트
rye run pytest
```
