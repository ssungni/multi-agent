# lec05_03_writer — 리포트 작성 + Evaluator 내장 도구 시스템

> 리서치 결과를 기반으로 섹션을 작성하고, 각 도구에 내장된 Evaluator 자기 루프로 품질을 보장합니다.

## 개요

이 강의에서는 리서치 결과를 기반으로 **구조화된 리포트를 작성하는 Writer Subagent**를 구현합니다.

Writer Subagent는 다음 흐름으로 동작합니다:
1. Orchestrator로부터 Outline with research results (아웃라인과 리서치 결과를 함께) 수신
2. Section write tool (LLM)을 호출하여 각 섹션 콘텐츠 작성
3. Section write tool 내장 Evaluator (LLM) 자기 루프로 섹션 품질 검증 및 재작성
4. 모든 섹션 완료 후 Report polish tool (LLM)을 호출하여 최종 리포트 통합
5. Report polish tool 내장 Evaluator (LLM) 자기 루프로 전체 리포트 품질 검증 및 수정

## 핵심 개념

### 왜 필요한가
리서치 데이터를 단순히 나열하는 것이 아니라, 읽기 좋은 **구조화된 리포트**로 변환해야 합니다.
개별 섹션의 품질뿐만 아니라 전체 리포트의 일관성도 검증해야 합니다.

### 무엇을 배우는가
**Evaluator 내장 도구** 패턴을 학습합니다.
각 LLM 도구(Section write tool, Report polish tool)가 자신의 Evaluator (LLM) 자기 루프를 내부에 보유하여 독립적으로 품질을 검증합니다.

### 어떻게 동작하는가
1. Section write tool (LLM)로 각 섹션의 콘텐츠 작성 (리서치 데이터 활용)
2. Section write tool 내장 Evaluator (LLM)가 섹션 품질 평가 → 미달 시 재작성 (자기 루프)
3. 모든 섹션 완료 후 Report polish tool (LLM)로 최종 리포트 통합
4. Report polish tool 내장 Evaluator (LLM)가 전체 리포트 품질 평가 → 미달 시 수정 (자기 루프)

## 아키텍처 / 흐름도

```
                    Orchestrator
                         │
               Outline with research results
                         │
                         ▼
                  Writer Subagent
                  ┌──────┴──────┐
                  │             │
                  ▼             ▼
     Section write tool (LLM)   Report polish tool (LLM)
     ┌──────────────────┐       ┌──────────────────┐
     │  Evaluator (LLM) │◄──┐   │  Evaluator (LLM) │◄──┐
     │  자기 루프       │   │   │  자기 루프       │   │
     └──────────────────┘   │   └──────────────────┘   │
              │ Pass         └── Fail (재작성)            └── Fail (수정)
              ▼
        (모든 섹션 완료)
              │
              ▼ (Report polish tool로 이동)
                         │
                         ▼
                    Final Report
```

Writer Subagent는 **Evaluator 내장 도구** 패턴을 사용합니다:
- **Section write tool (LLM)** 내장 Evaluator: 개별 섹션의 리서치 활용도, 인용, 가독성 검증 후 자기 루프
- **Report polish tool (LLM)** 내장 Evaluator: 전체 리포트의 일관성, 흐름, 중복 검증 후 자기 루프

## 코드 읽기 순서

이 모듈은 Evaluator 내장 도구 패턴을 사용하므로, 다음 순서로 읽으면 이해하기 쉽습니다:

1. **schemas.py** - 리포트 데이터 구조 이해
2. **state.py** - Writer Subagent 상태 구조 파악
3. **prompts.py** - 에이전트와 Evaluator의 역할 확인
4. **evaluator.py** - 두 가지 Evaluator의 평가 로직 이해
5. **tools.py** - 섹션 작성 및 리포트 통합 도구 확인
6. **agent.py** - 전체 흐름과 도구 내장 Evaluator 자기 루프 이해
7. **main.py** - 실제 사용 예제 확인

## 파일 구조

```
lec05_03_writer/
├── schemas.py      # ReportSection, FinalReport 스키마
├── state.py        # WriterState (상태 관리)
├── prompts.py      # 시스템 프롬프트, Evaluator 프롬프트
├── tools.py        # WriteSectionTool, FinalizeReportTool
├── evaluator.py    # SectionEvaluator, ReportEvaluator (LLM 기반 품질 평가)
├── agent.py        # WriterAgent 구현
├── __init__.py     # 모듈 export
├── main.py         # 통합 데모
└── README.md       # 이 문서
```

## 각 파일의 역할

### `schemas.py` - 리포트 스키마

- `ReportSection`: 개별 섹션 (title, content, sources)
- `FinalReport`: 최종 리포트 (title, sections 리스트, references)

### `state.py` - WriterState

`BaseAgentState`를 확장한 Writer 전용 상태:
- `outline`: 입력 아웃라인 (OutlinerAgent 결과)
- `section_research`: 섹션별 리서치 결과 맵
- `written_sections`: 작성된 섹션 맵 (섹션 제목 → ReportSection)
- `final_report`: 최종 통합 리포트
- `section_evaluation_feedback`: 섹션별 평가 피드백
- `report_evaluation_passed`: 리포트 전체 평가 통과 여부

### `prompts.py` - 프롬프트 정의

- `WRITER_SYSTEM_PROMPT`: 에이전트의 역할, 작성 가이드라인, 품질 기준
- `SECTION_EVALUATOR_PROMPT`: 섹션 품질 평가 기준 (리서치 활용도, 인용, 가독성)
- `REPORT_EVALUATOR_PROMPT`: 리포트 전체 평가 기준 (일관성, 흐름, 중복)

### `tools.py` - 작성 도구

- `WriteSectionTool`: 개별 섹션의 콘텐츠를 작성하고 상태에 저장
- `FinalizeReportTool`: 모든 섹션을 통합하여 최종 리포트 생성

### `evaluator.py` - 도구 내장 Evaluator

- `SectionEvaluator`: Section write tool (LLM) 내부에서 동작하는 Evaluator — 개별 섹션의 리서치 활용도, description 커버리지, 인용 정확성, 가독성 평가 후 자기 루프
- `ReportEvaluator`: Report polish tool (LLM) 내부에서 동작하는 Evaluator — 전체 리포트의 문체 일관성, 논리적 흐름, 섹션 간 연결, 중복 여부 평가 후 자기 루프

### `agent.py` - Writer Subagent

`BaseAgent[WriterState]`를 확장한 핵심 에이전트:
- `setup()`: 상태 초기화, Section write tool/Report polish tool 등록
- `_should_stop()`: `report_evaluation_passed`이거나 `max_iterations` 도달 시 종료
- `_hook_post_step()`: 각 도구 내장 Evaluator 기반 자기 루프 피드백 구현
  - **Section write tool 내장 Evaluator**: `write_section` 호출 시 섹션 품질 검증 후 자기 루프
  - **Report polish tool 내장 Evaluator**: `finalize_report` 호출 시 전체 품질 검증 후 자기 루프

## 이전 강의 대비 변경점

| 항목 | lec05_02 (ResearcherAgent) | lec05_03 (Writer Subagent) |
|------|---------------------------|---------------------------|
| 역할 | 정보 수집 (리서치) | 콘텐츠 생성 (작성) |
| Evaluator 구조 | RequiredInfo + Pipeline (별도 컴포넌트) | 각 도구에 Evaluator 내장 (자기 루프) |
| 피드백 루프 | 정의 검증 + 충분성 검증 | Section write tool 내 루프 + Report polish tool 내 루프 |
| 서브에이전트 | SearchAgent | 없음 (단일 에이전트) |
| 출력 | SectionResearch 맵 | FinalReport |

## 사용 예제

```python
from lec05_01_outliner.schemas import Outline, OutlineSection
from lec05_02_researcher.schemas import SectionResearch
from lec05_03_writer import WriterAgent

# 아웃라인 및 리서치 결과 준비
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

section_research = {
    "글로벌 시장 규모": SectionResearch(
        section_title="글로벌 시장 규모",
        summary="The global generative AI market reached $67.2B...",
        # ...
    ),
}

# WriterAgent 설정 및 실행
agent = await WriterAgent.setup(
    outline=outline,
    section_research=section_research,
    model="claude-4.5-sonnet",
    max_iterations=20,
)
await agent.run()

# 결과 확인
print(agent.state.final_report.title)
print(agent.state.report_evaluation_passed)
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec05-03
```

실행 시 다음이 수행됩니다:
1. 데모 아웃라인(3개 섹션)과 리서치 결과로 Writer Subagent 초기화
2. Section write tool (LLM)을 통해 각 섹션 콘텐츠 작성
3. Section write tool 내장 Evaluator (LLM) 자기 루프로 섹션 품질 검증 (미달 시 재작성)
4. 모든 섹션 완료 후 Report polish tool (LLM)로 최종 리포트 통합
5. Report polish tool 내장 Evaluator (LLM) 자기 루프로 전체 리포트 품질 검증 (미달 시 수정)
6. 최종 리포트 출력

## 학습 포인트

1. **리서치 데이터 활용 작성**: 수집된 정보를 자연스럽게 통합하여 콘텐츠 작성
2. **Evaluator 내장 도구 패턴**: 별도 컴포넌트가 아닌 각 도구 내부에 Evaluator를 내장하여 자기 루프로 품질 검증
3. **Section write tool 내장 Evaluator 기준**: 리서치 활용도, description 커버리지, 인용 정확성, 가독성
4. **Report polish tool 내장 Evaluator 기준**: 문체 일관성, 논리적 흐름, 중복 제거, 톤 일관성

## 참고

- BaseAgent 인터페이스: `lec04_01_base_agent/base.py`
- 입력 스키마: `lec05_01_outliner/schemas.py`, `lec05_02_researcher/schemas.py`
- Architecture: `archiecture/writer_agent.md`
- 이 에이전트를 사용하는 에이전트: `lec06_01_orchestrator/` (Milestone 7)

---

## 강의 네비게이션

← [이전: lec05_02_researcher - 섹션별 리서치](../lec05_02_researcher/README.md) | [다음: lec06_01_orchestrator - 전체 파이프라인 오케스트레이션 →](../lec06_01_orchestrator/README.md)
