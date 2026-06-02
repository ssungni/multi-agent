# lec05_01_outliner — 아웃라인 생성 + Evaluator 피드백 루프

> Orchestrator로부터 주제를 받아 Search/Fetch 도구로 정보를 수집하고, Evaluator 피드백 루프로 아웃라인 품질을 보장하는 서브에이전트입니다.

## 개요

이 강의에서는 사용자 주제로부터 **구조화된 리포트 아웃라인을 생성하는 Outliner 서브에이전트**를 구현합니다.

Outliner 서브에이전트는 다음 흐름으로 동작합니다:
1. Orchestrator로부터 주제를 입력받음
2. Search tool로 관련 정보 수집 (필요 시 반복 호출)
3. Fetch tool로 특정 URL의 전체 내용 수집 (선택적)
4. Outline generate tool로 아웃라인 생성
5. Outline generate tool 내부 Evaluator(LLM)가 품질 검증 → 미달 시 재생성 (자기 피드백 루프)
6. 최종 아웃라인을 Orchestrator에 반환

## 핵심 개념

### 왜 필요한가
리포트 작성의 첫 단계는 구조화된 아웃라인입니다. 한 번에 완벽한 아웃라인을 만들기 어려우므로,
LLM 기반 **Evaluator**가 품질을 검증하고 피드백을 제공하는 루프가 필요합니다.

### 무엇을 배우는가
**서브에이전트 + Evaluator 자기 피드백 루프** 패턴을 학습합니다.
서브에이전트가 도구를 선택적으로 호출하며 정보를 수집하고, Outline generate tool 내부 Evaluator가 품질을 평가하여 재생성을 유도합니다.

### 어떻게 동작하는가
1. Orchestrator로부터 주제(Topic) 수신
2. Outliner 서브에이전트가 Search tool 호출 → 검색 결과 수집
3. 필요 시 Fetch tool 호출 → URL 전체 내용 수집
4. Outline generate tool(LLM) 호출 → 아웃라인 생성
5. Outline generate tool 내부 Evaluator(LLM)가 품질 평가 → Pass/Fail + 피드백
6. Fail이면 피드백을 반영하여 재생성 (Evaluator 자기 루프 반복)
7. 최종 아웃라인을 Orchestrator에 반환

## 아키텍처 / 흐름도

```
                        Orchestrator
                             ↕
                    Outliner 서브에이전트
                   /          |          \
          Search tool    Fetch tool    Outline generate tool (LLM)
          (검색 쿼리        (URL →           ↑ Evaluator (LLM) ↓
           → 결과)         전체 내용)        (자기 피드백 루프)
```

Outliner 서브에이전트는 **단일 Evaluator 자기 피드백 루프** 구조를 가집니다:
- **서브에이전트 자율 판단**: Search tool과 Fetch tool을 필요에 따라 스스로 선택하여 호출
- **Evaluator 자기 루프**: Outline generate tool 내부 Evaluator(LLM)가 아웃라인 품질을 평가하고, 미달 시 재생성 유도

## 코드 읽기 순서

이 모듈을 처음 학습할 때 다음 순서로 코드를 읽으면 이해하기 쉽습니다:

1. **schemas.py** - 아웃라인 데이터 구조 이해
2. **state.py** - 에이전트 상태 구조 파악
3. **prompts.py** - 서브에이전트와 Evaluator의 역할 확인
4. **evaluator.py** - 아웃라인 품질 평가 로직 이해
5. **tools.py** - 아웃라인 생성 도구 구현 확인
6. **agent.py** - 전체 흐름과 피드백 루프 통합 이해
7. **main.py** - 실제 사용 예제 확인

## 파일 구조

```
lec05_01_outliner/
├── schemas.py      # Outline, OutlineSection 스키마
├── state.py        # OutlinerState (상태 관리)
├── prompts.py      # 시스템 프롬프트, Evaluator 프롬프트
├── tools.py        # GenerateOutlineTool
├── evaluator.py    # OutlineEvaluator (LLM 기반 품질 평가)
├── agent.py        # OutlinerAgent 구현
├── __init__.py     # 모듈 export
├── main.py         # 통합 데모
└── README.md       # 이 문서
```

## 각 파일의 역할

### `schemas.py` - 아웃라인 스키마

- `OutlineSection`: 개별 섹션 (title, description, subsections)
- `Outline`: 전체 아웃라인 (title, sections 리스트)

### `state.py` - OutlinerState

`BaseAgentState`를 확장한 Outliner 전용 상태:
- `reference_documents`: 수집된 참조 문서 리스트
- `outline`: 생성된 아웃라인 (Outline | None)
- `evaluation_feedback`: Evaluator의 피드백 메시지
- `evaluation_passed`: 평가 통과 여부

### `prompts.py` - 프롬프트 정의

- `OUTLINER_SYSTEM_PROMPT`: 서브에이전트의 역할, Search/Fetch 도구 활용 전략, 아웃라인 생성 지침
- `EVALUATOR_PROMPT`: 아웃라인 품질 평가 기준

### `tools.py` - GenerateOutlineTool

LLM이 호출하는 도구로, 수집된 정보를 기반으로 구조화된 아웃라인을 생성합니다.
- 아웃라인을 `state.outline`에 저장
- 저장 후 OutlineEvaluator를 자동 호출하여 품질 평가

### `evaluator.py` - OutlineEvaluator

LLM 기반으로 아웃라인 품질을 평가합니다.

**평가 기준:**
- 섹션 개수 (3~7개)
- Description의 구체성
- 섹션 간 중복 여부
- 논리적 흐름과 구조

평가 결과(`EvaluationResult`)에 따라 통과 또는 피드백과 함께 재생성을 유도합니다.

### `agent.py` - OutlinerAgent

`BaseAgent[OutlinerState]`를 확장한 핵심 서브에이전트:
- `setup()`: 상태 초기화, SearchTool/FetchTool/GenerateOutlineTool 등록
- `_should_stop()`: `evaluation_passed`이거나 `max_iterations` 도달 시 종료
- 서브에이전트가 스스로 Search tool / Fetch tool 호출 여부를 판단
- Evaluator 자기 루프는 GenerateOutlineTool 내부에서 처리

## 이전 강의 대비 변경점

| 항목 | lec04_01 (BaseAgent) | lec05_01 (OutlinerAgent) |
|------|---------------------|--------------------------|
| Agent 유형 | 단순 예제 (Calculator) | 실용 에이전트 (아웃라인 생성) |
| Tool | CalculatorTool, FinalAnswerTool | SearchTool, FetchTool, GenerateOutlineTool |
| 종료 조건 | max_iterations만 | evaluation_passed + max_iterations |
| 평가 시스템 | 없음 | OutlineEvaluator (LLM 기반) |
| 피드백 루프 | 없음 | Evaluator 자기 피드백 루프 |

## 사용 예제

```python
from lec05_01_outliner import OutlinerAgent

# OutlinerAgent 설정 및 실행
agent = await OutlinerAgent.setup(
    topic="2025년 생성형 AI 시장 동향",
    model="claude-4.5-sonnet",
    max_iterations=10,
)
await agent.run()

# 결과 확인
print(agent.state.outline)          # 생성된 아웃라인
print(agent.state.evaluation_passed) # 평가 통과 여부
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec05-01
```

실행 시 다음이 수행됩니다:
1. 데모 주제("2025년 생성형 AI 시장 동향")로 Outliner 서브에이전트 초기화
2. Search tool 호출을 통한 관련 정보 수집
3. 필요 시 Fetch tool 호출로 특정 URL 내용 수집
4. Outline generate tool 호출로 아웃라인 생성
5. Outline generate tool 내부 Evaluator 평가 → 미달 시 재생성 (반복)
6. 최종 아웃라인 출력

## 학습 포인트

1. **서브에이전트 패턴**: Orchestrator가 서브에이전트에 작업을 위임하고 결과를 받는 구조 이해
2. **도구 자율 선택**: 서브에이전트가 Search tool / Fetch tool을 상황에 따라 스스로 선택하여 호출
3. **Evaluator 자기 피드백 루프**: Outline generate tool 내부 Evaluator(LLM)가 품질을 평가하고 재생성을 유도
4. **종료 조건 커스터마이징**: `_should_stop()` 오버라이드를 통한 평가 기반 종료 로직
5. **Tool 내부에서 Evaluator 호출**: GenerateOutlineTool → OutlineEvaluator 연쇄 패턴

## 참고

- BaseAgent 인터페이스: `lec04_01_base_agent/base.py`
- 공통 도구: `lec04_02_tools/`
- Architecture: `archiecture/outliner_agent.md`
- 이 에이전트의 결과를 사용하는 에이전트: `lec05_02_researcher/`

---

## 강의 네비게이션

← [이전: lec04_02_tools - 공통 도구 구현](../lec04_02_tools/README.md) | [다음: lec05_02_researcher - 섹션별 리서치 →](../lec05_02_researcher/README.md)
