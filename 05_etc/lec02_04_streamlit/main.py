"""Lecture 02-04 실행 진입점 - Streamlit 채팅 인터페이스 시작.

이 모듈은 Streamlit 채팅 앱을 실행하는 CLI 진입점입니다.
`streamlit run` 명령을 프로그래밍 방식으로 호출하여
lec02_04_streamlit/app.py를 실행합니다.

학습 포인트:
    1. Streamlit 앱의 실행 구조
       - streamlit.cli를 통한 프로그래밍 방식 실행
       - `streamlit run <script>` 명령의 내부 동작
    2. Streamlit의 session_state 기반 상태 관리
       - 페이지 리렌더링 간 대화 이력 유지
       - dict 기반의 간단한 상태 저장소
    3. LiteLLM Router와 Streamlit의 통합
       - async LLM 호출을 동기 generator로 변환
       - st.write_stream을 활용한 실시간 스트리밍 표시

실행 방법:
    rye run lec02-04

채팅 흐름:
    브라우저 열림 (localhost:8501)
        └── 사이드바: 모델 선택 (claude-4.5-sonnet, gpt-5, ...)
        └── 채팅 입력창에 메시지 입력
              └── st.session_state에 사용자 메시지 저장
              └── st.chat_message("user")로 메시지 표시
              └── LiteLLM Router.acompletion(stream=True) 호출
                    └── async stream → 동기 generator 변환
                    └── st.write_stream()으로 실시간 표시
              └── st.session_state에 어시스턴트 응답 저장
        └── 페이지 리렌더링 시 session_state에서 이력 복원

참고:
    - Streamlit 앱: lec02_04_streamlit/app.py
    - LiteLLM Router: lec02_01_litellm/router.py
    - LLM 설정: lec02_01_litellm/config.py
"""

import sys
from pathlib import Path


def main() -> None:
    """Streamlit 채팅 앱을 실행합니다.

    streamlit.web.cli 모듈의 main_run 함수를 사용하여
    lec02_04_streamlit/app.py를 Streamlit 서버로 실행합니다.
    """
    from streamlit.web import cli as stcli

    app_path = str(Path(__file__).parent / "app.py")
    sys.argv = ["streamlit", "run", app_path, "--server.headless", "true"]
    stcli.main()


if __name__ == "__main__":
    main()
