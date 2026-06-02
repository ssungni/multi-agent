# lec07_02_ask_user — AskUserQuestion HITL Tool

> HITL 메커니즘을 활용하여 실행 중 사용자에게 구조화된 질문을 하는 범용 도구를 구현합니다.

## 개요

이 강의에서는 `AskUserQuestionTool`을 활용하여 실제 HITL (Human-In-The-Loop) 시나리오를 시연합니다. lec06_02_hitl에서 구현한 HITL Base 메커니즘을 기반으로, 두 가지 HITL 모드(tool_call, tool_result)가 공존하는 Report Generation Agent를 구현합니다.

## 핵심 개념

### 왜 필요한가
lec06_02의 HITL은 특정 도구(AskOutlineApprovalTool)에 하드코딩된 질문만 가능했습니다.
**어떤 상황에서든** 사용자에게 질문할 수 있는 **범용 도구**가 필요합니다.

### 무엇을 배우는가
1. LLM이 **질문 내용과 선택지를 동적으로 생성**하여 사용자에게 전달하는 `AskUserQuestionTool` 패턴
2. **tool_call 모드**: `_execute_tool_calls()`로 사용자 응답을 포함하여 도구를 재실행하는 패턴
3. **두 가지 HITL 모드의 공존**: tool_call(ask_user_question)과 tool_result(ask_outline_approval)

### 어떻게 동작하는가

#### tool_call 모드 (ask_user_question)
1. LLM이 `ask_user_question` 도구 호출 (질문/선택지를 LLM이 생성)
2. Tool이 answers가 비어있으면 `ExtendedHITLData(mode="tool_call")` 반환 → 루프 중단
3. 사용자가 선택지 중 하나를 선택하거나 커스텀 입력
4. `_resume_hitl()`이 `_execute_tool_calls()`로 answers가 채워진 상태로 도구 재실행
6. Tool이 Q&A 콘텐츠를 반환 → LLM이 다음 행동 결정

#### tool_result 모드 (ask_outline_approval)
1. LLM이 `ask_outline_approval` 도구 호출 (아웃라인 텍스트 전달)
2. Tool이 `ExtendedHITLData(mode="tool_result")` 반환 → 루프 중단
3. 사용자가 승인/거부 결정
4. `_resume_hitl()`이 payload를 JSON으로 tool message에 주입
5. 도구는 재실행되지 않음

## 이전 강의와 비교

| 항목 | lec06_02 (HITL Base) | lec07_02 (AskUserQuestion) |
|------|---------------------|---------------------------|
| HITL 모드 | tool_result만 | tool_call + tool_result |
| 질문 생성 | 도구에 하드코딩 | LLM이 동적으로 생성 |
| 질문 구조 | 자유 형식 | question + header + options + multiSelect |
| 용도 | 확인/거부 (Yes/No) | 범용 사용자 질문 |
| 선택지 | 없음 | 구조화된 옵션 + Other(커스텀 입력) |
| _resume_hitl() | payload를 JSON으로 주입 | _execute_tool_calls()로 도구 재실행 |

**학습 목표**:
1. `AskUserQuestionTool` 사용법 이해
2. tool_call 모드와 tool_result 모드의 차이 이해
3. 두 가지 HITL 모드가 공존하는 에이전트 구현

## 아키텍처 / 흐름도

```
User: "AI에 대한 리포트를 작성해줘" (의도적으로 모호함)
        ↓
LLM → ask_user_question (tool_call HITL interrupt)
        ↓
User answers (e.g., "생성형 AI", "시장 동향", "2025년")
        ↓
_resume_hitl():
  _execute_tool_calls() — 도구 재실행 (answers 포함)
        ↓
LLM → call_outliner → 아웃라인 생성
        ↓
LLM → ask_outline_approval (tool_result HITL interrupt)
        ↓
User approves
        ↓
_resume_hitl():
  payload를 JSON으로 tool message에 직접 주입
        ↓
LLM → call_researcher → call_writer → final_answer → COMPLETE
```

## 코드 읽기 순서

이 강의를 이해하기 위한 권장 코드 읽기 순서:

1. **hitl.py** - ExtendedHITLData 구조와 tool_call/tool_result 모드 이해
2. **state.py** - ExtendedHITLData를 지원하는 확장된 에이전트 상태
3. **ask_user.py** - AskUserQuestionTool 구현과 HITLData 통합 방식 이해
4. **base.py** - ExtendedBaseAgent의 _resume_hitl() 오버라이드 (tool_call 모드)
5. **main.py** - 두 가지 HITL 모드가 공존하는 실행 흐름 확인

## 파일 구조

```
lec07_02_ask_user/
├── hitl.py           # ExtendedHITLData — tool_call 모드 지원
├── state.py          # ExtendedAgentState, ExtendedOrchestratorState
├── ask_user.py       # AskUserQuestionTool implementation
├── base.py           # ExtendedBaseAgent — _resume_hitl() (tool_call 모드)
├── main.py           # 통합 실행 예제 (ReportAgent with dual HITL)
└── README.md         # 이 문서
```

### 각 파일의 역할

#### `hitl.py`
- `ExtendedHITLData`: tool_call 모드를 추가 지원하는 HITL 인터럽트 데이터
  - `mode="tool_result"`: 사용자가 결과를 직접 제공 (도구 재실행 없음)
  - `mode="tool_call"`: 사용자 답변으로 도구를 재실행
- `ExtendedToolResult`: ExtendedHITLData를 지원하는 도구 실행 결과

#### `state.py`
- `ExtendedAgentState`: `hitl_interrupts: list[ExtendedHITLData]`를 지원하는 상태
- `ExtendedOrchestratorState`: 워크플로우 필드 포함 (outline, research_results 등)

#### `ask_user.py`
- `AskUserQuestionTool`: 실행 중 사용자에게 질문하는 도구
- `AskUserQuestion`: 질문 구조 (question, header, multiSelect, options)
- `AskUserQuestionOption`: 선택지 옵션 (label, description)
- `AskUserQuestionPayload`: HITL 페이로드 (questions, answers)
- **HITL 통합**: answers가 비어있으면 `ExtendedHITLData(mode="tool_call")` 반환, 있으면 Q&A 콘텐츠 반환

#### `base.py`
- `ExtendedBaseAgent`: tool_call 모드를 지원하는 확장된 기본 에이전트
- `_resume_hitl()` 오버라이드:
  - **tool_call**: `_execute_tool_calls()`로 사용자 응답을 포함하여 도구 재실행
  - **tool_result**: payload를 JSON으로 tool message에 주입 (기존 동작)
- `_hook_post_llm_call()`: HITLData → ExtendedHITLData 변환 훅

#### `main.py`
- `ReportAgent`: 두 가지 HITL 모드를 지원하는 Report Generation Agent
- `get_user_answers()`: ask_user_question HITL 인터럽트 처리 (답변 수집)
- `process_ask_outline_approval_interrupt()`: ask_outline_approval HITL 인터럽트 처리
- `process_hitl_interrupts()`: 도구 이름에 따라 적절한 핸들러로 위임
- `run_report_agent()`: HITL 루프를 포함한 Agent 실행

## _resume_hitl()의 tool_call 모드 처리 (핵심)

```python
elif hitl_data.mode == "tool_call":
    # 사용자 응답을 포함하여 도구 재실행을 위한 tool_call 빌드
    tool_calls.append(
        ChatCompletionMessageToolCallParam(
            id=hitl_data.tool_call_id,
            type="function",
            function={
                "name": hitl_data.tool_name,
                "arguments": json.dumps(hitl_data.payload),
            },
        )
    )

# _execute_tool_calls()로 도구 재실행
if tool_calls:
    tool_results, nested_hitl_interrupts = await self._execute_tool_calls(tool_calls)
    if nested_hitl_interrupts:
        raise Exception(f"Nested HITL not supported: ...")
    tool_messages.extend(tool_results)
```

## HITLData Payload 구조

`AskUserQuestionTool`의 HITL 페이로드 구조:

```python
ExtendedHITLData(
    mode="tool_call",
    tool_name="ask_user_question",
    payload={
        "questions": [
            {
                "question": "어떤 AI 분야에 초점을 맞출까요?",
                "header": "AI 분야",
                "multiSelect": False,
                "options": [
                    {"label": "생성형 AI", "description": "GPT, Claude 등 생성형 AI 기술"},
                    {"label": "컴퓨터 비전", "description": "이미지/영상 인식 기술"},
                    {"label": "자연어처리", "description": "텍스트 이해 및 생성 기술"}
                ]
            }
        ],
        "answers": []  # 사용자 응답 후 채워짐
    }
)
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec07-02
```

### 실행 흐름

1. Agent가 "AI에 대한 리포트를 작성해줘" 쿼리로 시작 (의도적으로 모호함)
2. LLM이 `ask_user_question` 호출 → HITL interrupt (tool_call 모드)
3. 사용자가 AI 분야, 범위, 대상 등을 선택/입력
4. `_resume_hitl()`: `_execute_tool_calls()` → Q&A 콘텐츠 반환
5. LLM이 명확해진 주제로 `call_outliner` 호출 → 아웃라인 생성
6. LLM이 `ask_outline_approval` 호출 → HITL interrupt (tool_result 모드)
7. 사용자가 아웃라인 승인
8. `_resume_hitl()`: payload를 JSON으로 tool message에 주입
9. LLM이 `call_researcher` → `call_writer` → `final_answer` 호출
10. 최종 리포트 출력

---

## 강의 네비게이션

← [이전 강의: lec06_02_hitl - HITL Base 메커니즘](../lec06_02_hitl/README.md) | [다음 강의: lec08_03_quality - Agent 퀄리티 개선 →](../lec08_03_quality/README.md)
