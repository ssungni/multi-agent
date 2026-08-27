"""Streamlit 기반 LLM 채팅 인터페이스.

LiteLLM Router를 활용한 간단한 채팅 UI를 구현합니다.
lec02 시리즈(기초 인프라)에 맞게, 복잡한 Agent 연동 없이
Streamlit + LiteLLM 기본 사용법을 다룹니다.

주요 기능:
    - st.session_state를 이용한 대화 이력 관리
    - lec02_01_litellm의 CustomRouter를 통한 LLM 호출
    - st.chat_input / st.chat_message를 활용한 채팅 UI
    - Streaming 응답 실시간 표시
    - 사이드바에서 모델 선택 기능

학습 포인트:
    1. Streamlit의 session_state 기반 상태 관리
       - 페이지 리렌더링 간 데이터 유지 방법
    2. st.chat_input / st.chat_message 컴포넌트 사용법
       - 채팅 UI 구성의 기본 패턴
    3. LiteLLM Router를 통한 스트리밍 응답 처리
       - async generator를 Streamlit에서 동기적으로 처리하는 방법
    4. st.write_stream을 활용한 실시간 스트리밍 표시
"""

import asyncio
from collections.abc import Generator
from typing import Any

import streamlit as st

from lec02_02_langfuse.router import router

# ── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(
    page_title="LLM Chat - Lecture 02-04",
    page_icon="💬",
    layout="centered",
)

st.title("LLM Chat Interface")
st.caption("lec02_02_litellm의 Router를 활용한 간단한 채팅 데모")

# ── 사이드바: 모델 선택 ────────────────────────────────────────
AVAILABLE_MODELS = [
    "claude-4.5-sonnet",
    "claude-4.5-haiku",
    "gpt-5",
    "gpt-5-mini",
    "gemini-3-flash",
    "gemini-3-pro",
]

with st.sidebar:
    st.header("설정")
    selected_model = st.selectbox(
        "모델 선택",
        AVAILABLE_MODELS,
        index=0,
        help="LiteLLM Router에 등록된 모델 중 하나를 선택합니다.",
    )
    st.divider()
    st.markdown(
        "**사용 가능한 모델:**\n"
        "- `claude-4.5-sonnet` (Anthropic)\n"
        "- `claude-4.5-haiku` (Anthropic)\n"
        "- `gpt-5` (OpenAI)\n"
        "- `gpt-5-mini` (OpenAI)\n"
        "- `gemini-3-flash` (Google)\n"
        "- `gemini-3-pro` (Google)\n"
    )
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()


# ── 세션 상태 초기화 ──────────────────────────────────────────
# st.session_state는 Streamlit의 핵심 상태 관리 메커니즘입니다.
# 페이지가 리렌더링되어도 데이터가 유지됩니다.
if "messages" not in st.session_state:
    st.session_state.messages = []


# ── 대화 이력 표시 ─────────────────────────────────────────────
# session_state에 저장된 이전 메시지들을 채팅 버블로 렌더링합니다.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ── LLM 스트리밍 호출 함수 ───────────────────────────────────────
def stream_llm_response(
    model: str,
    messages: list[dict[str, str]],
) -> Generator[str, None, None]:
    """LiteLLM Router를 통해 LLM 스트리밍 응답을 생성합니다.

    Streamlit의 st.write_stream은 동기 generator를 요구하므로,
    async streaming 응답을 동기 generator로 변환합니다.

    Args:
        model: 사용할 LLM 모델명 (예: "claude-4.5-sonnet")
        messages: OpenAI 형식의 대화 메시지 리스트

    Yields:
        LLM 응답의 각 텍스트 청크
    """
    loop = asyncio.new_event_loop()

    async def _get_stream() -> Any:
        """비동기 스트리밍 응답을 가져옵니다."""
        return await router.acompletion(
            model=model,
            messages=messages,
            stream=True,
        )

    try:
        stream = loop.run_until_complete(_get_stream())
        aiter = stream.__aiter__()

        async def _anext() -> Any:
            """async iterator에서 다음 청크를 하나 가져옵니다."""
            return await aiter.__anext__()

        # 청크를 하나씩 가져와서 즉시 yield하여 실시간 스트리밍을 구현합니다.
        while True:
            try:
                chunk = loop.run_until_complete(_anext())
            except StopAsyncIteration:
                break
            if chunk.choices and chunk.choices[0].delta:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
    finally:
        loop.close()


# ── 사용자 입력 처리 ──────────────────────────────────────────
# st.chat_input은 채팅 입력창을 렌더링하고, 사용자 입력을 반환합니다.
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 1. 사용자 메시지를 세션에 저장하고 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. LLM 호출 및 스트리밍 응답 표시
    with st.chat_message("assistant"):
        # OpenAI 형식의 메시지 리스트 구성
        api_messages = [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
        ]

        # st.write_stream은 generator/iterator를 받아 실시간으로 텍스트를 표시합니다.
        response = st.write_stream(
            stream_llm_response(
                model=selected_model,
                messages=api_messages,
            )
        )

    # 3. 어시스턴트 응답을 세션에 저장
    st.session_state.messages.append({"role": "assistant", "content": response})
