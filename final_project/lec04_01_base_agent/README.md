# lec04_01_base_agent — Agentic Loop 구현

> LLM이 도구를 선택하고 실행하는 Think → Act → Observe 루프의 핵심 패턴을 구현합니다.

## 개요

이 강의에서는 **Agentic Loop 패턴**을 구현합니다.

Agent는 다음과 같은 루프를 반복합니다:
1. LLM을 호출하여 다음 행동을 결정
2. Tool을 실행하여 외부 시스템과 상호작용
3. 결과를 기반으로 다시 LLM 호출 (목표 달성까지 반복)

이 강의의 코드는 핵심 패턴과 설정을 포함한 완전한 BaseAgent 구현입니다.

## 핵심 개념

### 왜 필요한가
LLM은 단일 호출로는 복잡한 작업을 수행할 수 없습니다.
외부 도구(검색, 계산, API 호출 등)를 선택하고 실행하는 **루프**가 필요합니다.

### 무엇을 배우는가
**Think → Act → Observe** 패턴의 Agentic Loop를 구현합니다.
LLM이 도구를 호출하고, 결과를 관찰하고, 다음 행동을 결정하는 반복 구조를 학습합니다.

### 어떻게 동작하는가
1. LLM이 `tool_calls`를 반환 (Think)
2. Agent가 해당 도구를 실행 (Act)
3. 결과를 다시 LLM에 전달 (Observe)
4. LLM이 다음 행동을 결정 — 목표 달성까지 반복

## 아키텍처 / 흐름도

Agentic Loop의 핵심 실행 흐름:

```
┌─────────────────────────────────────────────────────────────┐
│                         run()                               │
│                           │                                 │
│                           ↓                                 │
│                   _should_stop()?                           │
│                      │        │                             │
│                      │ No     │ Yes → Exit                  │
│                      ↓        │                             │
│            _execute_single_step()                           │
│                      │                                      │
│                      ↓                                      │
│            _hook_pre_llm_call()                             │
│                      │                                      │
│            (메시지 리스트 반환)                                │
│                      │                                      │
│                      ↓                                      │
│               _call_llm()                                   │
│          (streaming/non-streaming)                          │
│                      │                                      │
│                      ↓                                      │
│           _hook_post_llm_call()                             │
│                      │                                      │
│              (LLM 응답 처리)                                  │
│                      │                                      │
│                      ↓                                      │
│          _execute_tool_calls()                              │
│                      │                                      │
│           (병렬 tool 실행)                                    │
│                      │                                      │
│                      ↓                                      │
│            _hook_post_step()                                │
│                      │                                      │
│              (후처리 작업)                                     │
│                      │                                      │
│                      └──────┐                               │
│                             │                               │
└─────────────────────────────┼───────────────────────────────┘
                              │
                              └─→ (loop back to _should_stop())
```

## 코드 읽기 순서

이 모듈을 처음 학습할 때는 다음 순서로 코드를 읽는 것을 권장합니다:

1. **`state.py`** - 에이전트가 관리하는 상태 구조 이해
2. **`tool.py`** - Tool의 추상화 인터페이스와 실행 메커니즘 파악
3. **`base.py`** - Agentic Loop의 핵심 구현 (run → hooks → tool execution)
4. **`example_agent.py`** - 구체적인 에이전트 구현 예제
5. **`main.py`** - 전체 시스템 통합 및 실행 데모

## 파일 구조

```
lec04_01_base_agent/
├── base.py             # BaseAgent 클래스 (Agentic Loop 구현)
├── state.py            # BaseAgentState (에이전트 상태 관리)
├── tool.py             # BaseTool, ToolResult (도구 추상화)
├── constant.py         # 상수 정의 (reasoning budget 등)
├── example_agent.py    # 예제 에이전트 구현
├── main.py             # 통합 데모
├── test_structure.py   # 구조 검증 테스트
└── README.md           # 이 문서
```

## 각 파일의 역할

### `base.py` - BaseAgent 클래스

에이전트 실행 루프의 완전한 구현을 제공합니다.

**핵심 컴포넌트:**
- `MaxIterationError`: 최대 반복 횟수 초과 시 발생하는 예외
- `BaseAgent[TState]`: 모든 에이전트의 추상 베이스 클래스

**메인 루프 메서드:**
- `run()`: `@observe` 데코레이터가 적용된 메인 에이전트 실행 루프
- `_should_stop()`: 종료 조건 확인 (최대 반복 횟수)
- `_execute_single_step()`: 단일 스텝 실행 오케스트레이션

**LLM 호출 메서드:**
- `_call_llm()`: 스트리밍/논스트리밍 분기 처리
- `_call_llm_non_streaming()`: 논스트리밍 LLM 호출
- `_call_llm_streaming()`: `thinking_blocks`/`reasoning_content`를 지원하는 스트리밍 LLM 호출
- `_build_llm_params()`: 공통 LLM 파라미터 빌드
- `_merge_delta_tool_calls()`: 스트리밍 tool call 델타 병합
- `_merge_delta_thinking_blocks()`: thinking block 델타 병합

**Tool 실행 메서드:**
- `_execute_tool_calls()`: `asyncio.gather`를 사용한 병렬 tool 실행
- `_tool_call()`: 단일 tool 실행
- `_find_tool_by_name()`: tool 이름으로 검색 헬퍼
- `_build_tool_message()`: tool 응답 메시지 빌드

**Hook 메서드 (Virtual):**
- `_hook_pre_llm_call()`: 메시지 리스트 반환
- `_hook_post_llm_call()`: LLM 응답 처리, tool 실행
- `_hook_post_step()`: 스텝 후처리 작업

**Helper 메서드:**
- `_append_message()`: state에 메시지 추가
- `_extend_messages()`: state에 메시지 확장

### `constant.py` - 에이전트 상수
- `NUM_REASONING_BUDGET_TOKENS`: Extended Thinking을 위한 reasoning budget

### `tool.py` - BaseTool, ToolResult
- `ToolResult`: Tool 실행 결과 (`content`, `artifact`)
- `BaseTool`: Tool 추상 클래스 (JSON schema 기반 파라미터 정의)
- `call()`: Langfuse 모니터링과 함께 도구 실행
- `_execute()`: 서브클래스에서 구현할 추상 메서드

### `example_agent.py` - 예제 구현

다음을 보여주는 구체적인 에이전트 구현 예제:
- `BaseAgent` 확장
- `setup()` classmethod 구현
- 커스텀 tool 정의 (`CalculatorTool`, `FinalAnswerTool`)
- 에이전트 루프 실행

### `test_structure.py` - 구조 검증

필요한 모든 메서드와 속성이 존재하는지 검증하는 테스트입니다.

## 이후 강의에서 추가되는 기능

이 강의에서 다루지 않는 기능은 이후 강의에서 점진적으로 추가됩니다:
1. **비용 추적**: lec08_04에서 추가
2. **HITL (Human-in-the-Loop)**: lec06_02에서 추가
3. **Context Engineering**: lec08_05에서 추가

현재 포함된 기능:
- 스트리밍 및 논스트리밍 지원
- Extended Thinking (`thinking_blocks`, `reasoning_content`)
- `asyncio.gather`를 사용한 병렬 tool 실행
- LLM이 tool을 호출하지 않을 때 에러 메시지 주입
- Langfuse observation 데코레이터

## 사용 예제

```python
from typing import Any
from typing_extensions import Self

from lecture.lec04_01_base_agent import BaseAgent, BaseAgentState, BaseTool, ToolResult


class MyTool(BaseTool[BaseAgentState]):
    name = "my_tool"
    description = "Example tool"
    parameters = {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Input value"},
        },
        "required": ["input"],
        "additionalProperties": False,
    }

    async def _execute(self, state: BaseAgentState, **kwargs: Any) -> ToolResult:
        _ = state  # 이 도구에서는 상태를 사용하지 않음
        input_value: str = kwargs["input"]
        return ToolResult(content=f"Result: {input_value}", artifact=None)

class MyAgent(BaseAgent[BaseAgentState]):
    @classmethod
    async def setup(cls, query: str) -> Self:
        self = await super().setup()
        self.state = BaseAgentState(messages=[...])
        self.tools = [MyTool()]
        self.max_iterations = 10
        self.model = "claude-4-sonnet"
        self.stream = False
        self._initialized = True
        return self

# Run the agent
agent = await MyAgent.setup(query="Hello")
await agent.run()
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec04-01
```

실행 시 다음이 수행됩니다:
1. Langfuse 모니터링 초기화
2. 수학 쿼리를 가진 SimpleAgent 생성
3. Agentic Loop 실행
4. 전체 대화 기록 표시
5. Tool 호출 및 결과 표시

예상 출력 내용:
- 시스템 프롬프트 설정
- 사용자 쿼리
- LLM 추론 및 tool 선택
- Calculator tool 실행
- 최종 답변 전달

### 테스트 실행

구현 검증을 위한 구조 테스트:
```bash
rye run python -m lecture.lec04_01_base_agent.test_structure
```

---

## 강의 내비게이션

← [이전 강의: lec02_04_streamlit](../lec02_04_streamlit/README.md) | [다음 강의: lec04_02_tools](../lec04_02_tools/README.md) →