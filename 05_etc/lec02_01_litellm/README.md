# lec02_01_litellm — LiteLLM Multi-Provider Routing

> 여러 LLM 프로바이더를 단일 인터페이스로 통합하고, Fallback으로 안정성을 확보합니다.

## 개요

## 핵심 개념

### 왜 필요한가
LLM 프로바이더는 OpenAI, Anthropic, Google 등 여러 곳이 있고, 각각 SDK와 API 형식이 다릅니다.
프로바이더 장애 시 서비스가 중단되는 문제도 있습니다.

### 무엇을 배우는가
LiteLLM Router를 사용하여 **단일 인터페이스**로 여러 프로바이더를 통합하고, **자동 Fallback**으로 안정성을 확보하는 패턴을 학습합니다.

### 어떻게 동작하는가
1. `router.py`에서 모델별 프로바이더와 Fallback 순서를 설정
2. `router.acompletion(model="gpt-5", ...)`으로 호출
3. 실패 시 자동으로 다음 Fallback 모델로 재시도

이 강의에서는 LiteLLM Router를 사용하여 여러 LLM 프로바이더(OpenAI, Claude, Gemini)를 통합하고 자동 fallback을 구현하는 방법을 다룹니다.

## 아키텍처 / 흐름도

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LiteLLM Router Architecture                      │
└─────────────────────────────────────────────────────────────────────────┘

    User Application
         │
         │ router.acompletion(model="gpt-5", messages=...)
         ▼
    ┌──────────────────┐
    │  LiteLLM Router  │ ← 멀티 프로바이더 추상화 계층
    └──────────────────┘
         │
         ├─────────────┬─────────────┬─────────────┐
         │             │             │             │
         ▼             ▼             ▼             ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ OpenAI  │  │Anthropic│  │ Google  │  │ Gemini  │
    │  GPT-5  │  │ Claude  │  │ Gemini  │  │ Flash   │
    └─────────┘  └─────────┘  └─────────┘  └─────────┘
         │             │             │             │
         │ 실패 시 Fallback →│             │
         │                   └→ 실패 시 →  │
         │                                 └→ 최종 시도

┌─────────────────────────────────────────────────────────────────────────┐
│ Fallback Strategy (자동 우선순위)                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ • gpt-5              → claude-4-sonnet → gemini-2.5-flash              │
│ • claude-4-sonnet    → gpt-5           → gemini-2.5-flash              │
│ • gemini-2.5-flash   → gpt-5           → claude-4-sonnet               │
└─────────────────────────────────────────────────────────────────────────┘
```

## 코드 읽기 순서 (Recommended Reading Order)

강의 이해를 위한 권장 파일 읽기 순서:

1. **config.py** - 환경 변수 로딩 및 API 키 관리 (`.env` 설정 확인)
2. **router.py** - LiteLLM Router 초기화 및 멀티 프로바이더 설정
3. **main.py** - 실제 사용 예제 (동일 프롬프트, 다른 모델 비교)

## 학습 목표

1. **LiteLLM Router 설정**: 여러 LLM 프로바이더를 단일 인터페이스로 통합
2. **Fallback 전략**: 모델 실패 시 자동으로 대체 모델로 전환
3. **API 키 관리**: 환경 변수를 통한 안전한 API 키 관리

## 파일 구조

```
lec02_01_litellm/
├── __init__.py         # 모듈 exports
├── config.py           # 환경 변수 설정 (.env 로딩)
├── router.py           # LiteLLM Router 설정 (멀티 프로바이더 + fallback)
├── main.py             # 데모 스크립트
└── README.md           # 이 문서
```

### 각 파일의 역할

#### `config.py`
- `.env` 파일에서 환경 변수를 로딩하여 전역 설정을 제공
- `LLMConfig`: OpenAI, Anthropic, Google API 키 관리
- **싱글톤 인스턴스** (`llm_config`)를 통해 다른 모듈에서 import하여 사용

#### `router.py`
- LiteLLM Router를 초기화하고 멀티 프로바이더 라우팅 설정
- **지원 모델**: GPT-5, GPT-5 Mini, GPT-4.1 Mini, Claude 4.5 Sonnet/Haiku/Opus, Gemini 3 Flash/Pro
- **Fallback 전략**: 모델 실패 시 자동으로 대체 모델로 전환
- **Context Window Fallback**: 입력이 너무 길 경우 더 큰 context를 지원하는 모델로 전환

#### `main.py`
- 멀티 프로바이더 호출 데모 (동일 프롬프트, 다른 모델)
- 각 모델의 응답 특성 비교

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec02-01
```

## 코드 사용 예제

### 기본 사용법

```python
from lec02_01_litellm.router import router

# 동기 호출
response = router.completion(
    model="gpt-5",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# 비동기 호출
response = await router.acompletion(
    model="claude-4-sonnet",
    messages=[{"role": "user", "content": "Explain AI."}]
)
print(response.choices[0].message.content)
```

### 지원하는 모델

- `gpt-5`: GPT-5 (OpenAI)
- `gpt-5-mini`: GPT-5 Mini (OpenAI)
- `gpt-4.1-mini`: GPT-4.1 Mini (OpenAI)
- `claude-4.5-sonnet`: Claude 4.5 Sonnet (Anthropic)
- `claude-4.5-haiku`: Claude 4.5 Haiku (Anthropic)
- `claude-4.5-opus`: Claude 4.5 Opus (Anthropic)
- `gemini-3-flash`: Gemini 3 Flash (Google)
- `gemini-3-pro`: Gemini 3 Pro (Google)

### Fallback 전략

모델 호출이 실패할 경우 자동으로 대체 모델로 전환됩니다:

- `gpt-5` → `claude-4.5-sonnet` → `gemini-3-flash`
- `gpt-5-mini` → `gemini-3-flash` → `gpt-5`
- `gpt-4.1-mini` → `gpt-5-mini` → `gemini-3-flash`
- `claude-4.5-sonnet` → `gpt-5` → `gemini-3-flash`
- `claude-4.5-haiku` → `claude-4.5-sonnet` → `gemini-3-flash`
- `claude-4.5-opus` → `claude-4.5-sonnet` → `gpt-5`
- `gemini-3-flash` → `gpt-5` → `claude-4.5-sonnet`
- `gemini-3-pro` → `gpt-5` → `claude-4.5-sonnet` → `claude-4.5-opus`

## 주요 개념

### model_name vs litellm_params.model

- **model_name**: Router에서 사용하는 별칭 (예: `"gpt-5"`)
- **litellm_params.model**: 실제 프로바이더 API에 전달되는 모델 식별자 (예: `"gpt-5"`)

이 분리를 통해:
1. 모델 버전 업데이트 시 `model_name`은 유지하고 `litellm_params.model`만 변경 가능
2. 동일 모델을 다른 API 키로 여러 번 등록 가능 (로드밸런싱)
3. 프로바이더별 명명 규칙 차이를 추상화

## 강의 네비게이션

```
← (없음 - 첫 강의) │ 현재: lec02_01_litellm │ 다음: lec02_02_langfuse →
```

**이전 강의**: 없음 (CH02의 첫 강의)

**이 강의**: LiteLLM Multi-Provider Router + Fallback 구현

**다음 강의**: [lec02_02_langfuse](../lec02_02_langfuse/README.md) - Langfuse를 통한 LLM 호출 모니터링 및 Observability
