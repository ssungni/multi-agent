# lec02_04_streamlit — Streamlit Chat UI

> LiteLLM Router를 활용한 웹 기반 채팅 인터페이스를 구현합니다.

## 개요

## 핵심 개념

### 왜 필요한가
CLI에서의 LLM 호출은 테스트에는 유용하지만, 실제 사용자에게는 직관적인 웹 UI가 필요합니다.

### 무엇을 배우는가
Streamlit의 채팅 컴포넌트를 사용하여 **멀티턴 대화**, **스트리밍 응답 표시**, **모델 선택** 기능을 갖춘 채팅 UI를 구현합니다.

### 어떻게 동작하는가
1. `st.session_state.messages`로 대화 이력 관리
2. `router.acompletion(stream=True)`로 스트리밍 호출
3. `st.write_stream()`으로 실시간 응답 표시

이 강의에서는 **LiteLLM Router를 활용한 간단한 Streamlit 채팅 인터페이스**를 구현합니다.

lec02 시리즈(기초 인프라)에 맞게, 복잡한 Agent 연동 없이 Streamlit + LiteLLM 기본 사용법을 다룹니다:
1. `st.session_state`를 이용한 대화 이력 관리
2. `st.chat_input` / `st.chat_message`를 활용한 채팅 UI
3. LiteLLM Router의 스트리밍 응답을 `st.write_stream`으로 실시간 표시
4. 사이드바에서 모델 선택 (Claude, GPT, Gemini)

## 아키텍처 / 흐름도

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  Streamlit Chat UI + LiteLLM Architecture               │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │   User Browser   │
    │  (웹 인터페이스)  │
    └──────────────────┘
            │
            │ 1. 사용자 입력 (st.chat_input)
            │ 2. 모델 선택 (st.sidebar.selectbox)
            ▼
    ┌──────────────────────────────────────┐
    │       Streamlit App (app.py)         │
    │                                      │
    │  ┌────────────────────────────────┐ │
    │  │   st.session_state.messages    │ │ ← 대화 이력 저장
    │  │   (멀티턴 대화 관리)            │ │
    │  └────────────────────────────────┘ │
    │                                      │
    │  ┌────────────────────────────────┐ │
    │  │  st.chat_message (버블 표시)   │ │ ← User/Assistant 메시지
    │  └────────────────────────────────┘ │
    │                                      │
    │  ┌────────────────────────────────┐ │
    │  │  st.write_stream (스트리밍)     │ │ ← 실시간 응답 표시
    │  └────────────────────────────────┘ │
    └──────────────────────────────────────┘
            │
            │ router.acompletion(model, messages, stream=True)
            ▼
    ┌──────────────────┐
    │  LiteLLM Router  │ ← lec02_01_litellm.router
    └──────────────────┘
            │
            ├─────────────┬─────────────┬─────────────┐
            ▼             ▼             ▼             ▼
       [OpenAI]      [Anthropic]    [Google]      [Gemini]
            │             │             │             │
            └─────────────┴─────────────┴─────────────┘
                        │
                        │ 스트리밍 응답 (chunk by chunk)
                        ▼
                User Browser (실시간 텍스트 표시)

┌─────────────────────────────────────────────────────────────────────────┐
│ Data Flow                                                               │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. User Input → st.session_state.messages.append(user_message)         │
│ 2. LiteLLM Router → async stream generator                             │
│ 3. Async → Sync conversion (asyncio.run)                               │
│ 4. st.write_stream(sync_generator) → 실시간 표시                        │
│ 5. st.session_state.messages.append(assistant_message)                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## 코드 읽기 순서 (Recommended Reading Order)

강의 이해를 위한 권장 파일 읽기 순서:

1. **app.py** - Streamlit 채팅 UI 구현 (session_state, chat_input, write_stream)
2. **main.py** - CLI 진입점 (`rye run lec02-04` 실행 시 호출됨)

## 파일 구조

```
lec02_04_streamlit/
├── app.py          # Streamlit 채팅 앱 구현
├── main.py         # CLI 진입점 (streamlit run 래퍼)
├── __init__.py     # 모듈 export
└── README.md       # 이 문서
```

## 각 파일의 역할

### `app.py` - Streamlit 채팅 앱

Streamlit의 채팅 컴포넌트를 사용한 LLM 채팅 인터페이스:
- **세션 상태 관리**: `st.session_state.messages`에 대화 이력 저장
- **채팅 UI**: `st.chat_input`으로 입력, `st.chat_message`로 버블 표시
- **스트리밍 응답**: LiteLLM Router의 async streaming을 동기 generator로 변환하여 `st.write_stream`으로 실시간 표시
- **모델 선택**: 사이드바에서 사용 가능한 모델 선택

### `main.py` - CLI 진입점

`streamlit.web.cli`를 사용하여 `app.py`를 Streamlit 서버로 실행합니다.
`rye run lec02-04` 명령으로 호출됩니다.

## 이전 강의 대비 변경점

| 항목 | lec02_02 (LiteLLM) | lec02_04 (Streamlit) |
|------|--------------------|-----------------------|
| 인터페이스 | CLI (터미널 출력) | 웹 UI (Streamlit) |
| 응답 방식 | 동기 완성 후 출력 | 스트리밍 실시간 표시 |
| 대화 이력 | 없음 (단발 호출) | session_state로 멀티턴 |
| 모델 선택 | 코드 내 하드코딩 | 사이드바 UI로 동적 선택 |

## 사용 예제

```python
# app.py의 핵심 패턴: LiteLLM 스트리밍 → Streamlit 표시
from lec02_01_litellm.router import router

# 1. LiteLLM Router로 스트리밍 호출
stream = await router.acompletion(
    model="claude-4.5-sonnet",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True,
)

# 2. 스트림에서 텍스트 청크 추출
async for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="")
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec02-04
```

실행 시 다음이 수행됩니다:
1. Streamlit 서버 시작 (기본 포트: 8501)
2. 브라우저에서 채팅 인터페이스 열림
3. 사이드바에서 모델 선택 가능
4. 채팅 입력창에 메시지 입력 후 Enter
5. LLM 응답이 스트리밍으로 실시간 표시

## 학습 포인트

1. **Streamlit session_state**: 페이지 리렌더링 간 상태 유지 패턴
2. **st.chat_input / st.chat_message**: Streamlit 채팅 UI 컴포넌트 사용법
3. **st.write_stream**: generator를 받아 실시간 텍스트 스트리밍 표시
4. **async → sync 변환**: Streamlit(동기)에서 LiteLLM(비동기) 스트리밍 처리

## 참고

- LiteLLM Router: `lec02_01_litellm/router.py`
- LLM 설정: `lec02_01_litellm/config.py`
- Streamlit 공식 문서: https://docs.streamlit.io/develop/api-reference/chat

## 강의 네비게이션

```
← lec02_03_vllm │ 현재: lec02_04_streamlit │ 다음: lec04_01_base_agent →
```

**이전 강의**: [lec02_03_vllm](../lec02_03_vllm/README.md) - vLLM 폐쇄망 LLM 서빙 (참고용)

**이 강의**: Streamlit Chat UI - LiteLLM 기반 웹 채팅 인터페이스

**다음 강의**: [lec04_01_base_agent](../lec04_01_base_agent/README.md) - BaseAgent 구현 (Think → Act → Observe Loop)
