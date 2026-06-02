# lec06_01_orchestrator — Multi-Agent 워크플로우 조율

> Subagent들을 조율하여 Outline → Research → Write 파이프라인을 관리합니다.

## 개요

이 강의에서는 **Subagent들을 조율하여 전체 리포트 생성 워크플로우를 관리하는 OrchestratorAgent**를 구현합니다.

## 핵심 개념

### 왜 필요한가
개별 Subagent(Outliner, Researcher, Writer)는 각자의 작업만 수행합니다.
이들을 **올바른 순서로 호출**하고 **데이터를 전달**하는 중앙 조율자가 필요합니다.

### 무엇을 배우는가
**Orchestrator 패턴**을 학습합니다.
OrchestratorAgent가 허브 역할을 하며 각 Subagent와 양방향으로 소통하고, 상태를 중앙에서 관리합니다.

### 어떻게 동작하는가
1. Phase 1: CallOutlinerTool → Outliner Subagent가 아웃라인 생성
2. Phase 2: CallResearcherTool → Researcher Subagent가 섹션별 리서치
3. Phase 3: CallWriterTool → Writer Subagent가 최종 리포트 작성
4. Phase 4: FinalAnswerTool → 사용자에게 결과 전달

OrchestratorAgent는 다음 흐름으로 동작합니다:
1. 사용자의 리포트 요청 수신
2. Outliner Subagent를 호출하여 구조화된 아웃라인 생성 (양방향 소통)
3. Researcher Subagent를 호출하여 섹션별 정보 수집 (양방향 소통)
4. Writer Subagent를 호출하여 최종 리포트 작성 (양방향 소통)
5. FinalAnswerTool로 최종 리포트를 사용자에게 전달

## 아키텍처 / 흐름도

```
                         User
                          │
                     Request (→)
                     Report  (←)
                          │
                    [Orchestrator]
                   ↗      ↑      ↖
                  ↙        ↓       ↘
    Outliner             Researcher            Writer
    Subagent             Subagent              Subagent
```

- Orchestrator는 허브(중심)로서 각 Subagent와 양방향으로 통신합니다.
- User → Orchestrator: 리포트 요청 (최초 1회)
- Orchestrator → User: 최종 리포트 전달 (FinalAnswerTool)
- Orchestrator ↔ 각 Subagent: 작업 요청 및 결과 반환 (양방향)
- 중간에 사용자 개입(HITL)은 없으며, HITL 통합은 `lec06_02_hitl/`에서 다룹니다.

## 코드 읽기 순서

1. `state.py` - OrchestratorState, Phase Enum 정의
2. `prompts.py` - Orchestrator 시스템 프롬프트
3. `tools.py` - Subagent 호출 도구 (CallOutlinerTool, CallResearcherTool, CallWriterTool, FinalAnswerTool)
4. `agent.py` - OrchestratorAgent 구현
5. `main.py` - 통합 데모 실행

## 파일 구조

```
lec06_01_orchestrator/
├── state.py        # OrchestratorState, Phase Enum
├── prompts.py      # ORCHESTRATOR_SYSTEM_PROMPT
├── tools.py        # CallOutlinerTool, CallResearcherTool, CallWriterTool, FinalAnswerTool
├── agent.py        # OrchestratorAgent 구현
├── __init__.py     # 모듈 export
├── main.py         # 통합 데모
└── README.md       # 이 문서
```

## 각 파일의 역할

### `state.py` - OrchestratorState, Phase

- `Phase`: 워크플로우 단계 Enum (OUTLINE_GENERATION, RESEARCH, WRITING, COMPLETE)
- `OrchestratorState`: 전체 워크플로우 상태 (original_request, outline, research_results, final_report 등)

### `prompts.py` - 시스템 프롬프트

- `ORCHESTRATOR_SYSTEM_PROMPT`: 워크플로우 순서, Phase별 행동 지침, 도구 사용 규칙

### `tools.py` - Subagent 호출 도구

4가지 도구를 제공합니다:

- `CallOutlinerTool`: Outliner Subagent를 호출하여 아웃라인 생성
- `CallResearcherTool`: Researcher Subagent를 호출하여 섹션별 리서치 수행
- `CallWriterTool`: Writer Subagent를 호출하여 최종 리포트 작성
- `FinalAnswerTool`: 최종 리포트를 사용자에게 전달

모든 Subagent 호출 도구는 **Constructor Injection** 패턴을 사용하여 순환 import를 방지합니다.

### `agent.py` - OrchestratorAgent

`BaseAgent[OrchestratorState]`를 확장한 핵심 에이전트:
- `setup()`: 상태 초기화, 4개 도구 등록
- `_should_stop()`: `Phase.COMPLETE`이거나 `max_iterations` 도달 시 종료
- Orchestrator는 자체 Evaluator가 없음 (각 Subagent가 독립적으로 평가 수행)

## 이전 강의 대비 변경점

| 항목 | lec05_01~03 (Subagents) | lec06_01 (OrchestratorAgent) |
|------|--------------------------|------------------------------|
| Agent 역할 | 개별 작업 수행 (아웃라인/리서치/작성) | Subagent 조율 및 워크플로우 관리 |
| Tool 유형 | 직접 실행 도구 (Search, Fetch 등) | Subagent 호출 도구 (CallOutliner 등) |
| 종료 조건 | evaluation_passed + max_iterations | Phase.COMPLETE + max_iterations |
| 평가 시스템 | 각 agent별 Evaluator | 없음 (Subagent에 위임) |
| 상태 관리 | 단일 작업 상태 | 전체 파이프라인 상태 (Phase 추적) |
| Import 패턴 | 직접 import | Constructor Injection (순환 import 방지) |

## 사용 예제

```python
from lec06_01_orchestrator import OrchestratorAgent

# OrchestratorAgent 설정 및 실행
agent = await OrchestratorAgent.setup(
    user_request="2025년 생성형 AI 시장 동향에 대한 리포트를 작성해주세요.",
    model="claude-4.5-sonnet",
    max_iterations=20,
)
await agent.run()

# 결과 확인
print(agent.state.current_phase)   # Phase.COMPLETE
print(agent.state.final_report)    # 최종 리포트
print(agent.state.outline)         # 생성된 아웃라인
print(agent.state.research_results)  # 리서치 결과
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec06-01
```

실행 시 다음이 수행됩니다:
1. 데모 주제("2025년 생성형 AI 시장 동향")로 OrchestratorAgent 초기화
2. Outliner Subagent 호출 → 아웃라인 생성 (웹 검색 + 평가 루프)
3. Researcher Subagent 호출 → 섹션별 리서치 수행 (필요 정보 정의 + 검색)
4. Writer Subagent 호출 → 최종 리포트 작성 (섹션 작성 + 평가 루프)
5. FinalAnswerTool 호출 → 최종 리포트 전달
6. 워크플로우 결과 및 최종 리포트 출력

## 학습 포인트

1. **Subagent 호출 패턴**: Subagent를 Tool로 감싸서 호출하는 패턴 (Constructor Injection)
2. **워크플로우 상태 관리**: Phase Enum을 사용한 단계별 상태 전환
3. **허브 앤 스포크 구조**: Orchestrator가 허브로서 각 Subagent와 양방향으로 소통하며 전체 데이터 흐름을 관리
4. **평가 위임**: Orchestrator 자체는 Evaluator가 없고, 각 Subagent가 독립적으로 품질 평가

## 참고

- BaseAgent 인터페이스: `lec04_01_base_agent/base.py`
- OutlinerAgent: `lec05_01_outliner/agent.py`
- ResearcherAgent: `lec05_02_researcher/agent.py`
- WriterAgent: `lec05_03_writer/agent.py`
- Architecture: `archiecture/orchestrator.md`
- HITL 통합 버전: `lec06_02_hitl/`

---

## 강의 네비게이션

← [이전 강의: lec05_03_writer](../lec05_03_writer/README.md) | [다음 강의: lec06_02_hitl](../lec06_02_hitl/README.md) →
