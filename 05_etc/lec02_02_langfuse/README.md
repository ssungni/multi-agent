# lec02_02_langfuse — Langfuse Observability

> LLM 호출을 자동으로 기록하고, 비용/성능을 대시보드에서 추적합니다.

## 개요

## 핵심 개념

### 왜 필요한가
LLM 호출은 비용이 발생하고, 응답 품질이 불안정할 수 있습니다.
어떤 호출이 얼마나 비용이 들었는지, 어디서 실패했는지 추적할 수 없으면 운영이 어렵습니다.

### 무엇을 배우는가
Langfuse를 LiteLLM에 통합하여 모든 LLM 호출을 **자동으로 기록**하고, **비용/토큰/레이턴시**를 추적하는 Observability 패턴을 학습합니다.

### 어떻게 동작하는가
1. `router.py`에서 LiteLLM Router를 import하고 Langfuse 콜백을 등록
2. `@observe` 데코레이터로 함수 단위 트레이싱
3. `trace_id`/`parent_observation_id`로 `@observe` trace와 LiteLLM 콜백을 연결
4. 모든 LLM 호출이 Langfuse 대시보드에 자동 기록

## 이전 강의와 비교

| 항목 | lec02_01 (LiteLLM) | lec02_02 (Langfuse) |
|------|--------------------|--------------------|
| 핵심 기능 | Multi-Provider 통합 | + Observability 추가 |
| LLM 호출 추적 | 없음 | 자동 기록 (토큰, 비용, 레이턴시) |
| 에러 추적 | 없음 | 실패 콜백으로 자동 로깅 |
| 대시보드 | 없음 | Langfuse UI에서 시각화 |

이 강의에서는 Langfuse를 사용하여 LLM 호출을 모니터링하고 트레이싱하는 방법을 다룹니다. LiteLLM Router와 통합하여 모든 LLM 호출을 자동으로 기록하고 대시보드에서 시각화합니다.

## 아키텍처 / 흐름도

```
┌─────────────────────────────────────────────────────────────────────────┐
│               LiteLLM + Langfuse Observability Architecture             │
└─────────────────────────────────────────────────────────────────────────┘

    User Application
         │
         │ @observe 데코레이터로 함수 호출 트레이싱
         ▼
    ┌──────────────────┐
    │  Python Function │  ← langfuse_context.update_current_trace()
    │   (@observe)     │  ← langfuse_context.update_current_observation()
    └──────────────────┘
         │
         │ router.acompletion(...)
         ▼
    ┌──────────────────┐
    │  LiteLLM Router  │  ← lec02_02_langfuse/router.py에서 콜백 등록
    └──────────────────┘  ← metadata로 trace_id/parent_observation_id 전달
         │
         ├─────────────┬─────────────┬─────────────┐
         ▼             ▼             ▼             ▼
    [OpenAI]      [Anthropic]    [Google]      [Gemini]
         │             │             │             │
         └─────────────┴─────────────┴─────────────┘
                        │
                        │ 자동 기록 (토큰, 비용, 레이턴시, 에러)
                        ▼
                ┌────────────────┐
                │    Langfuse    │  ← https://cloud.langfuse.com
                │   Dashboard    │
                └────────────────┘
                        │
                        ├─ Traces (전체 실행 흐름)
                        ├─ Observations (함수별 span)
                        ├─ Metrics (응답시간, 토큰, 비용)
                        └─ Metadata (프롬프트, 응답, 태그)

┌─────────────────────────────────────────────────────────────────────────┐
│ Trace vs Observation Hierarchy                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Trace (lecture02_02_main_demo)                                         │
│   ├─ Observation: call_model_gpt5                                      │
│   │    └─ LiteLLM Generation (자동 기록)                               │
│   ├─ Observation: call_model_claude                                    │
│   │    └─ LiteLLM Generation (자동 기록)                               │
│   └─ Observation: call_model_gemini                                    │
│        └─ LiteLLM Generation (자동 기록)                               │
└─────────────────────────────────────────────────────────────────────────┘
```

## 코드 읽기 순서 (Recommended Reading Order)

강의 이해를 위한 권장 파일 읽기 순서:

1. **config.py** - Langfuse API 키 설정 (`.env` 파일 확인 필수)
2. **observability.py** - Langfuse 클라이언트 초기화, `@observe` 데코레이터, `langfuse_context` 사용법
3. **router.py** - LiteLLM Router import 및 Langfuse 콜백 등록
4. **main.py** - LiteLLM + Langfuse 통합 예제 (trace 연동 및 실제 트레이싱)

## 학습 목표

1. **Langfuse 설정**: Langfuse 클라이언트 초기화 및 환경 변수 관리
2. **LiteLLM 통합**: LiteLLM callback을 통한 자동 모니터링
3. **Trace/Observation 패턴**: `@observe` 데코레이터와 `langfuse_context`를 활용한 상세 트레이싱

## 파일 구조

```
lec02_02_langfuse/
├── __init__.py         # 모듈 exports
├── config.py           # 환경 변수 설정 (.env 로딩)
├── observability.py    # Langfuse 모니터링 설정 (@observe 데코레이터)
├── router.py           # LiteLLM Router + Langfuse 콜백 등록
├── main.py             # 통합 데모 (LiteLLM + Langfuse)
└── README.md           # 이 문서
```

### 각 파일의 역할

#### `config.py`
- `.env` 파일에서 환경 변수를 로딩하여 전역 설정을 제공
- `LangfuseConfig`: Langfuse Public/Secret Key 및 Host 설정
- **싱글톤 인스턴스** (`langfuse_config`)를 통해 다른 모듈에서 import하여 사용

#### `observability.py`
- Langfuse 클라이언트 초기화 및 설정
- `@observe` 데코레이터를 통한 함수 단위 트레이싱
- `langfuse_context`를 통해 trace/observation 메타데이터 추가
- **학습 목표**: Langfuse 통합 패턴 이해

#### `router.py`
- `lec02_01_litellm`의 Router를 가져와서 Langfuse 콜백을 등록
- import만 하면 `litellm.success_callback`/`failure_callback`이 자동 설정
- **학습 목표**: 콜백 설정을 Router와 함께 관리하여 관심사 분리

#### `main.py`
- LiteLLM Router와 Langfuse를 통합한 데모
- `lec02_02_langfuse.router`에서 콜백이 등록된 router를 import
- `trace_id`/`parent_observation_id`로 `@observe` trace와 LiteLLM generation을 연결
- 모든 호출은 Langfuse에 자동으로 기록되어 대시보드에서 확인 가능

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec02-02
```

### Langfuse 대시보드 확인 사항

데모 실행 후 https://cloud.langfuse.com 에서 다음을 확인할 수 있습니다:

1. **Traces**: 전체 실행 흐름
   - `lecture02_02_main_demo` trace 하위에 모델별 observation

2. **Metrics**:
   - 모델별 평균 응답 시간 (latency)
   - 토큰 사용량 (input/output/total tokens)
   - 비용 (USD)

3. **Metadata**:
   - 프롬프트 길이, 응답 길이
   - 모델명, finish_reason
   - 커스텀 태그 및 메타데이터

## 코드 사용 예제

### 기본 사용법

```python
from lec02_02_langfuse.observability import setup_langfuse, observe, langfuse_context
from lec02_02_langfuse.router import router  # import 시 Langfuse 콜백 자동 등록

# 1. Langfuse 초기화
setup_langfuse()

# 2. @observe 데코레이터로 함수 트레이싱
@observe(capture_input=True, capture_output=True)
async def generate_response(prompt: str) -> str:
    # langfuse_context로 메타데이터 추가
    langfuse_context.update_current_trace(
        user_id="user_123",
        session_id="session_abc",
        metadata={"model": "gpt-5"},
    )

    # trace_id/parent_observation_id를 전달하여 @observe trace와 LiteLLM generation 연결
    response = await router.acompletion(
        model="gpt-5",
        messages=[{"role": "user", "content": prompt}],
        metadata={
            "trace_id": langfuse_context.get_current_trace_id(),
            "parent_observation_id": langfuse_context.get_current_observation_id(),
        },
    )

    return response.choices[0].message.content
```

### Trace vs Observation

- **Trace**: 전체 요청 레벨의 메타데이터
  - `langfuse_context.update_current_trace()`로 설정
  - user_id, session_id, tags 등

- **Observation**: 현재 함수 호출(span) 레벨의 메타데이터
  - `langfuse_context.update_current_observation()`으로 설정
  - 특정 단계의 상세 정보 (모델명, 프롬프트 길이 등)

### 중첩 호출 패턴

```python
@observe(capture_input=True, capture_output=True)
async def process_request(user_input: str) -> str:
    langfuse_context.update_current_trace(
        user_id="user_123",
        tags=["production"],
    )

    # 하위 함수 호출이 자동으로 하위 span으로 기록됨
    result = await call_model("gpt-5", user_input)
    return result

@observe(capture_input=True, capture_output=True)
async def call_model(model_name: str, prompt: str) -> str:
    langfuse_context.update_current_observation(
        name=f"call_{model_name}",
        metadata={"model": model_name},
    )

    # metadata로 trace_id/parent_observation_id를 전달해야
    # LiteLLM generation이 @observe trace 트리 안에 연결됨
    response = await router.acompletion(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        metadata={
            "trace_id": langfuse_context.get_current_trace_id(),
            "parent_observation_id": langfuse_context.get_current_observation_id(),
        },
    )

    return response.choices[0].message.content
```

## 주요 개념

### LiteLLM Callback Integration

`lec02_02_langfuse/router.py`에서 Langfuse 콜백을 등록합니다. import만 하면 자동으로 설정됩니다:

```python
# lec02_02_langfuse/router.py
import litellm
from lec02_01_litellm.router import router

litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]
```

이를 통해:
- 모델별 응답 시간 자동 기록
- 토큰 사용량 자동 추적
- 비용 자동 계산
- 에러 발생 시 자동 로깅

### @observe와 LiteLLM trace 연결

`@observe` 데코레이터와 LiteLLM 콜백은 **별도의 트레이싱 경로**입니다. `router.acompletion` 호출 시 `metadata`에 `trace_id`와 `parent_observation_id`를 전달해야 하나의 trace 트리로 연결됩니다:

```python
response = await router.acompletion(
    model=model_name,
    messages=[{"role": "user", "content": prompt}],
    metadata={
        "trace_id": langfuse_context.get_current_trace_id(),
        "parent_observation_id": langfuse_context.get_current_observation_id(),
    },
)
```

### @observe 데코레이터

함수에 `@observe` 데코레이터를 추가하면:
- 함수 호출이 Langfuse span으로 기록됨
- 입력/출력이 자동으로 캡처됨 (capture_input, capture_output)
- 중첩 호출이 부모-자식 관계로 시각화됨

### langfuse_context

현재 실행 중인 trace/observation에 메타데이터를 추가합니다:
- `update_current_trace()`: 전체 요청 레벨 메타데이터
- `update_current_observation()`: 현재 함수 호출 레벨 메타데이터

## 이전 단계와의 통합

이 모듈은 `lec02_02_langfuse/router.py`를 통해 `lec02_01_litellm`의 Router를 래핑합니다:

```python
# lec02_02_langfuse/router.py
from lec02_01_litellm.router import router  # 기존 Router import
litellm.success_callback = ["langfuse"]      # Langfuse 콜백 등록

# main.py 등 사용처에서는 래핑된 router를 import
from lec02_02_langfuse.router import router
```

이를 통해:
- `lec02_01_litellm`의 Router는 순수한 상태로 유지 (Langfuse 의존성 없음)
- Langfuse 콜백 설정이 Router와 함께 관리됨
- 사용처에서 import만 하면 콜백이 자동 등록 (설정 누락 방지)
- 관심사의 분리 (Separation of Concerns) 달성

## 강의 네비게이션

```
← lec02_01_litellm │ 현재: lec02_02_langfuse │ 다음: lec02_03_vllm →
```

**이전 강의**: [lec02_01_litellm](../lec02_01_litellm/README.md) - LiteLLM Multi-Provider Router + Fallback

**이 강의**: Langfuse Observability - LLM 호출 모니터링 및 트레이싱

**다음 강의**: [lec02_03_vllm](../lec02_03_vllm/README.md) - vLLM을 사용한 폐쇄망 오픈소스 LLM 서빙 (참고용)
