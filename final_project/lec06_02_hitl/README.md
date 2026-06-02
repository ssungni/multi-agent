# lec06_02_hitl — Human-In-The-Loop 메커니즘

> Agent 실행 중 사용자 입력이 필요할 때 일시 정지하고, 응답을 받아 재개하는 HITL 패턴을 구현합니다.

이 디렉토리는 HITL 메커니즘의 구현과 동작을 보여줍니다. HITL은 Agent가 실행 중 사용자 입력이 필요할 때 일시 정지하고, 응답을 받아 재개하는 메커니즘입니다.

## 핵심 개념

### 왜 필요한가
Agent가 자율적으로 작업을 수행하다가 **사용자 확인이 필요한 순간**이 있습니다.
예: 위험한 작업 전 확인, 모호한 요구사항 명확화, 아웃라인 승인 등.

### 무엇을 배우는가
Agent가 실행 중 **HITLData**를 반환하면 루프가 일시 정지되고,
사용자 응답을 받은 후 **_resume_hitl()**로 재개하는 패턴을 학습합니다.

### 어떻게 동작하는가
1. Tool이 `ToolResult(hitl_data=HITLData(...))`를 반환
2. Agent가 `hitl_interrupts`를 감지하고 루프 중단
3. 외부에서 사용자 응답을 수집하여 `hitl.payload`에 추가
4. `_resume_hitl()`로 재개 — mode에 따라 도구 재실행 또는 결과 주입

## 이전 강의와 비교

| 항목 | lec06_01 (Orchestrator + Subagent) | lec06_02 (HITL) |
|------|------------------------|-----------------|
| Agent 실행 | 자율 실행 (중단 없음) | 사용자 입력 시 일시 정지 |
| 사용자 개입 | 없음 | HITLData로 인터럽트 |
| ToolResult | content + artifact | + hitl_data 필드 추가 |
| BaseAgentState | iteration_count | + hitl_interrupts 필드 추가 |
| 재개 메커니즘 | 없음 | _resume_hitl() 메서드 추가 |

## 아키텍처 / 흐름도

```
Agent.run() → Tool returns HITLData
                   ↓
           _should_stop() → True (hitl_interrupts detected)
                   ↓
           User provides response
                   ↓
           _resume_hitl()
           ├── rejected → Rejection message injected
           ├── mode="tool_call" → Re-execute tool with modified args
           └── mode="tool_result" → Inject user response as tool message
                   ↓
           Agent.run() continues
```

## 코드 읽기 순서

1. `hitl.py` - HITLData 데이터 모델 정의
2. `tool.py` - ToolResult with hitl_data (lec04_01_base_agent/tool.py 확장)
3. `state.py` - BaseAgentState with hitl_interrupts (lec04_01_base_agent/state.py 확장)
4. `base.py` - BaseAgent with HITL support (lec04_01_base_agent/base.py 확장)
5. `ask_outline_approval.py` - AskOutlineApproval 도구 (tool_result 모드 HITL 예제)
6. `agent.py` - Orchestrator with HITL support
7. `main.py` - HITL 통합 실행 예제

## 파일 구조

```
lec06_02_hitl/
├── base.py                    # BaseAgent with HITL support (lec04_01_base_agent/base.py 확장)
├── state.py                   # BaseAgentState with hitl_interrupts (lec04_01_base_agent/state.py 확장)
├── tool.py                    # ToolResult with hitl_data (lec04_01_base_agent/tool.py 확장)
├── hitl.py                    # HITLData 클래스 (신규)
├── ask_outline_approval.py    # AskOutlineApproval 도구 (신규, tool_result 모드 HITL 예제)
├── main.py                    # HITL 통합 실행 예제 (신규)
└── README.md                  # 이 문서
```

### 각 파일의 역할

1. **hitl.py**: HITLData 데이터 모델
   - HITL 인터럽트를 표현하는 Pydantic 모델
   - `mode`: "tool_call" (인자 수정) 또는 "tool_result" (결과 직접 제공)
   - `payload`: HITL 데이터 (도구 인자 또는 결과)
   - `rejected`: 사용자가 거부한 경우 True

2. **tool.py**: ToolResult with hitl_data
   - lec04_01_base_agent/tool.py를 확장
   - `ToolResult.hitl_data` 필드 추가
   - 도구가 HITLData를 반환하면 Agent가 일시 정지

3. **state.py**: BaseAgentState with hitl_interrupts
   - lec04_01_base_agent/state.py를 확장
   - `hitl_interrupts` 필드 추가 (pending HITL 데이터 저장)

4. **base.py**: BaseAgent with HITL support
   - lec04_01_base_agent/base.py를 확장
   - `_should_stop()`: hitl_interrupts가 있으면 True 반환
   - `_execute_tool_calls()`: HITLData 수집
   - `_resume_hitl()`: 사용자 응답으로 재개

5. **main.py**: HITL 통합 실행 예제
   - ConfirmationTool: 위험한 작업 전 사용자 확인 요청
   - HITLDemoAgent: HITL 흐름 시연
   - 전체 HITL 흐름을 단계별로 출력

## lec04_01_base_agent에서의 변경사항

lec06_02_hitl은 lec04_01_base_agent의 코드를 확장하여 HITL 기능을 추가합니다.

### 1. hitl.py (신규)

```python
class HITLData(BaseModel):
    """HITL 인터럽트 데이터"""
    mode: Literal["tool_call", "tool_result"]
    tool_name: str
    tool_call_id: str = ""
    payload: dict[str, Any]
    rejected: bool = False
```

### 2. tool.py 변경사항

```python
class ToolResult(BaseModel):
    content: str
    artifact: Any = None
    hitl_data: HITLData | None = None  # [ADDED in lec06_02_hitl]
```

### 3. state.py 변경사항

```python
class BaseAgentState(BaseModel):
    model: str = "gpt-4"
    messages: list[ChatCompletionMessageParam] = []
    iteration_count: int = 0
    hitl_interrupts: list[HITLData] = []  # [ADDED in lec06_02_hitl]
```

### 4. base.py 변경사항

#### _should_stop()
```python
def _should_stop(self) -> bool:
    if self.state.iteration_count >= self.max_iterations:
        raise MaxIterationError(...)
    return bool(self.state.hitl_interrupts)  # [ADDED in lec06_02_hitl]
```

#### _hook_post_llm_call()
```python
async def _hook_post_llm_call(self, message: ...) -> None:
    self._append_message(message)
    if tool_calls := message.get("tool_calls", []):
        tool_messages, hitl_interrupts = await self._execute_tool_calls(...)  # [ADDED]
        self._extend_messages(tool_messages)
        self.state.hitl_interrupts = hitl_interrupts  # [ADDED in lec06_02_hitl]
```

#### _execute_tool_calls()
```python
async def _execute_tool_calls(
    self, tool_calls: list[...]
) -> tuple[list[...], list[HITLData]]:  # [ADDED: return hitl_interrupts]
    tool_messages = []
    hitl_interrupts = []  # [ADDED in lec06_02_hitl]

    # ... execute tools ...

    for tool_call, result in zip(tool_calls, tool_results):
        if result.hitl_data:  # [ADDED in lec06_02_hitl]
            result.hitl_data.tool_call_id = tool_call.get("id") or ""
            hitl_interrupts.append(result.hitl_data)
        else:
            tool_messages.append(self._build_tool_message(tool_call, result))

    return tool_messages, hitl_interrupts  # [ADDED in lec06_02_hitl]
```

#### _resume_hitl() (신규)
```python
async def _resume_hitl(self) -> None:
    """사용자 응답으로 HITL 재개

    세 가지 모드 처리:
    1. rejected=True: 사용자가 거부 → rejection 메시지 주입
    2. mode="tool_call": 수정된 인자로 도구 재실행
    3. mode="tool_result": 사용자가 직접 결과 제공
    """
    # ... implementation ...
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec06-02
```

## HITL 모드 비교

| Mode | 설명 | 재개 방식 | 사용 예시 |
|------|------|----------|----------|
| `tool_call` | 도구 인자 수정 후 재실행 | `payload` 수정 → 도구 재호출 | 확인 필요한 작업, 인자 수정 |
| `tool_result` | 사용자가 직접 결과 제공 | `payload`를 tool 메시지로 주입 | 수동 입력, 외부 데이터 |
| `rejected=True` | 사용자가 작업 거부 | rejection 메시지 주입 | 작업 취소 |

---

## 강의 네비게이션

← [이전 강의: lec06_01_orchestrator](../lec06_01_orchestrator/README.md) | [다음 강의: lec07_02_ask_user](../lec07_02_ask_user/README.md) →