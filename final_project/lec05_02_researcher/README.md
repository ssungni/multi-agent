# lec05_02_researcher — 섹션별 리서치 + Orchestrator-SubAgent 패턴

> Orchestrator-SubAgent 패턴으로 섹션별 독립적인 웹 리서치를 수행합니다.

## 개요

이 강의에서는 아웃라인의 각 섹션에 대해 **웹 리서치를 수행하는 Researcher Subagent**를 구현합니다.

Researcher Subagent는 **Orchestrator-SubAgent 패턴**을 적용합니다:
- **Researcher Subagent** (오케스트레이터): 섹션별 필요 정보를 정의하고 SearchAgent에 위임
- **SearchAgent** (서브에이전트): 개별 섹션에 대해 웹 검색 및 콘텐츠 수집 수행

하나의 Evaluator 기반 피드백 루프를 구현합니다:
1. **RequiredInfoEvaluator**: 필요 정보 정의의 품질 검증 (Researcher Subagent 레벨)

## 핵심 개념

### 왜 필요한가
아웃라인의 각 섹션은 서로 다른 주제를 다루므로, 섹션별 독립적인 리서치가 필요합니다.
단일 Agent로는 복잡도가 높아지므로 **서브에이전트에 위임**하는 패턴이 효과적입니다.

### 무엇을 배우는가
**Orchestrator-SubAgent 패턴**을 학습합니다.
Researcher Subagent(오케스트레이터)가 리서치 계획을 수립하고, SearchAgent(서브에이전트)에 섹션별 리서치를 위임합니다.

### 어떻게 동작하는가
1. Researcher Subagent가 섹션별 필요 정보를 정의 (RequiredInfoEvaluator로 검증)
2. 각 섹션에 SearchAgent 서브에이전트를 병렬로 생성하여 리서치 위임
3. SearchAgent가 필요 정보를 입력받아 웹 검색(Search tool) 및 콘텐츠 수집(Fetch tool) 수행
4. 모든 SearchAgent 결과를 Deduplication 단계에서 중복 제거
5. 최종 결과를 Orchestrator로 반환

## 아키텍처 / 흐름도

```
[researcher_agent.png 참고]

Outline
  │
  ▼
Required information for each section ◄─── Evaluator (LLM) 피드백 루프
  │
  ├──► Search Agent (섹션 1)  ─┐
  ├──► Search Agent (섹션 2)  ─┼──► Deduplication ──► Orchestrator
  └──► Search Agent (섹션 N)  ─┘
       (병렬 실행, "Research Subagent")

[search_agent.png 참고]

Researcher Subagent
  │ Required Information
  ▼
Search Agent ◄──► Search tool (Search query)
  │    ▲
  ▼    │
Fetch tool
```

이 에이전트는 **Orchestrator-SubAgent 패턴**을 적용합니다:
- **Researcher Subagent**: 전체 리서치 계획 수립, 필요 정보 정의(Evaluator 검증), 서브에이전트 관리
- **SearchAgent**: 필요 정보를 입력받아 Search tool / Fetch tool로 웹 검색 및 콘텐츠 수집 수행
- **Deduplication**: 병렬 SearchAgent의 결과를 취합한 뒤 중복 데이터를 제거하여 Orchestrator에 반환

## 코드 읽기 순서

이 모듈은 Orchestrator-SubAgent 패턴을 사용하므로, 다음 순서로 읽으면 이해하기 쉽습니다:

1. **schemas.py** - 리서치 데이터 구조 이해
2. **state.py** - Researcher Subagent(오케스트레이터) 상태 구조 파악
3. **search_agent_state.py** - SearchAgent(서브에이전트) 상태 구조 파악
4. **prompts.py**
5. **evaluator.py** - RequiredInfoEvaluator의 평가 로직 이해
6. **search_agent_tools.py** - 서브에이전트의 도구 구현 확인
7. **agent.py** - Researcher Subagent 전체 흐름 이해
8. **search_agent.py** - SearchAgent 구현 이해
9. **main.py** - 실제 사용 예제 확인

## 파일 구조

```
lec05_02_researcher/
├── schemas.py              # RequiredInfo, SectionResearch 스키마
├── state.py                # ResearcherState (오케스트레이터 상태)
├── search_agent_state.py   # SearchAgentState (서브에이전트 상태)
├── prompts.py              # 시스템 프롬프트, Evaluator 프롬프트
├── tools.py                # DefineRequiredInfoTool, CallSubagentSearchAgentTool
├── search_agent_tools.py   # SubmitResearchTool (서브에이전트 전용)
├── evaluator.py            # RequiredInfoEvaluator
├── agent.py                # ResearcherAgent (오케스트레이터)
├── search_agent.py         # SearchAgent (서브에이전트)
├── __init__.py             # 모듈 export
├── main.py                 # 통합 데모
└── README.md               # 이 문서
```

## 각 파일의 역할

### `schemas.py` - 리서치 스키마

- `RequiredInfo`: 섹션별 필요 정보 항목 (description, covered 여부)
- `SectionResearch`: 섹션 리서치 결과 (required_info, search_results, fetched_contents, summary)

### `state.py` - ResearcherState (오케스트레이터)

- `outline`: 입력 아웃라인 (OutlinerAgent 결과)
- `section_research_results`: 섹션별 리서치 결과 맵
- `reference_documents`: 수집된 참조 문서 리스트 (Deduplication 후)
- `required_info_evaluation_passed`: 필요 정보 정의 평가 통과 여부
- `all_research_complete`: 전체 리서치 완료 여부

### `search_agent_state.py` - SearchAgentState (서브에이전트)

SearchAgent 전용 상태로, 개별 섹션의 리서치 진행 상태를 관리합니다.

### `prompts.py` - 프롬프트 정의

- `RESEARCHER_SYSTEM_PROMPT`: Researcher Subagent 역할, 필요 정보 정의 지침
- `SEARCH_AGENT_SYSTEM_PROMPT`: SearchAgent 역할, 검색 전략 지침
- Evaluator 프롬프트: 필요 정보 평가 기준 (RequiredInfoEvaluator)

### `tools.py` - 오케스트레이터 도구

- `DefineRequiredInfoTool`: 섹션별 필요 정보를 정의하고 RequiredInfoEvaluator로 검증
- `CallSubagentSearchAgentTool`: SearchAgent 서브에이전트를 병렬로 생성하여 섹션 리서치 위임 후 Deduplication 수행
  - **Constructor injection** 패턴으로 순환 import 방지

### `search_agent_tools.py` - 서브에이전트 도구

- `SubmitResearchTool`: 웹 검색 및 콘텐츠 수집 결과를 제출

### `evaluator.py` - Evaluator

- `RequiredInfoEvaluator`: 정의된 필요 정보의 구체성, 커버리지 평가 (Researcher Subagent 레벨)

### `agent.py` - ResearcherAgent (오케스트레이터)

`BaseAgent[ResearcherState]`를 확장한 오케스트레이터 에이전트:
- `setup()`: 상태 초기화, DefineRequiredInfoTool/CallSubagentSearchAgentTool 등록
- `_should_stop()`: `all_research_complete`이거나 `max_iterations` 도달 시 종료
- Constructor injection으로 SearchAgent 클래스를 CallSubagentSearchAgentTool에 주입

### `search_agent.py` - SearchAgent (서브에이전트)

`BaseAgent[SearchAgentState]`를 확장한 서브에이전트:
- Researcher Subagent로부터 필요 정보(Required Information)를 입력받아 실행
- SearchTool(Search query 발송), FetchTool(콘텐츠 수집) 사용
- SubmitResearchTool로 수집 결과 제출

## 이전 강의 대비 변경점

| 항목 | lec05_01 (OutlinerAgent) | lec05_02 (ResearcherAgent) |
|------|-------------------------|---------------------------|
| 에이전트 구조 | 단일 에이전트 | Orchestrator + SubAgent |
| Evaluator | 1개 (OutlineEvaluator) | 1개 (RequiredInfoEvaluator) |
| 피드백 루프 | Evaluator 주도 1중 루프 | 필요 정보 정의 검증 루프 |
| 병렬 처리 | 검색 쿼리 병렬 | 섹션별 서브에이전트 병렬 위임 |
| 중복 제거 | 없음 | Deduplication (병렬 결과 취합 후) |
| 의존성 주입 | 없음 | Constructor injection (순환 import 방지) |

## 사용 예제

```python
from lec05_01_outliner.schemas import Outline, OutlineSection
from lec05_02_researcher import ResearcherAgent

# 아웃라인 준비 (OutlinerAgent 결과 또는 직접 생성)
outline = Outline(
    title="2025년 생성형 AI 시장 동향",
    sections=[
        OutlineSection(
            title="글로벌 시장 규모",
            description="2025년 글로벌 생성형 AI 시장 규모 분석...",
            subsections=["시장 규모 현황", "성장 전망"],
        ),
        # ...
    ],
)

# ResearcherAgent 설정 및 실행
agent = await ResearcherAgent.setup(
    outline=outline,
    model="claude-4.5-sonnet",
    max_iterations=15,
)
await agent.run()

# 결과 확인
for title, research in agent.state.section_research_results.items():
    print(f"{title}: {'완료' if research.research_complete else '진행 중'}")
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec05-02
```

실행 시 다음이 수행됩니다:
1. 데모 아웃라인(3개 섹션)으로 ResearcherAgent 초기화
2. 섹션별 필요 정보 정의 및 RequiredInfoEvaluator 평가
3. 평가 통과 후 섹션별 SearchAgent 서브에이전트 병렬 위임
4. 각 SearchAgent가 필요 정보를 입력받아 웹 검색(Search tool) → 콘텐츠 수집(Fetch tool) → 결과 제출 수행
5. 병렬 결과를 Deduplication으로 중복 제거
6. 전체 리서치 결과 출력

## 학습 포인트

1. **Orchestrator-SubAgent 패턴**: 복잡한 작업을 서브에이전트에 위임하는 구조
2. **Constructor Injection**: 순환 import를 방지하면서 서브에이전트 클래스를 도구에 주입
3. **Evaluator 피드백 루프**: 필요 정보 정의 단계에서 LLM 기반 평가로 품질을 검증하는 구조
4. **병렬 서브에이전트 실행**: 섹션별 SearchAgent를 동시에 실행하여 리서치 속도 향상
5. **Deduplication**: 병렬 에이전트의 결과를 취합한 뒤 중복 데이터를 제거하는 패턴
6. **상태 병합**: 서브에이전트의 결과를 오케스트레이터 상태에 병합하는 패턴

## 참고

- BaseAgent 인터페이스: `lec04_01_base_agent/base.py`
- 공통 도구: `lec04_02_tools/`
- 입력 스키마: `lec05_01_outliner/schemas.py`
- Architecture: `archiecture/researcher_agent.md`
- 이 에이전트의 결과를 사용하는 에이전트: `lec05_03_writer/` (Milestone 6)

---

## 강의 네비게이션

← [이전: lec05_01_outliner - 아웃라인 생성](../lec05_01_outliner/README.md) | [다음: lec05_03_writer - 리포트 작성 →](../lec05_03_writer/README.md)
