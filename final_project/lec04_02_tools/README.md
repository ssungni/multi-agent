# lec04_02_tools — 공통 도구 (SearchTool, FetchTool)

> 웹 검색과 콘텐츠 추출을 위한 실용 도구를 BaseTool로 구현합니다.

## 개요

이 강의에서는 Report Generation Agent에서 사용하는 **공통 도구(SearchTool, FetchTool)**를 구현합니다.

- **SearchTool**: Serper API를 사용한 웹 검색 도구 (복수 쿼리 병렬 검색)
- **FetchTool**: httpx + BeautifulSoup을 사용한 웹페이지 콘텐츠 추출 도구

이 도구들은 `BaseTool`을 확장하며, OutlinerAgent와 ResearcherAgent에서 웹 정보 수집에 사용됩니다.

## 핵심 개념

### 왜 필요한가
Agent가 실제 작업을 수행하려면 외부 세계와 상호작용할 도구가 필요합니다.
웹 검색과 콘텐츠 추출은 Report Generation의 핵심 도구입니다.

### 무엇을 배우는가
`BaseTool`을 확장하여 **SearchTool**(웹 검색)과 **FetchTool**(콘텐츠 추출)을 구현하고,
### 어떻게 동작하는가
1. SearchTool: Serper API로 복수 쿼리 병렬 검색 → `state.reference_documents`에 저장
2. FetchTool: httpx + BeautifulSoup으로 메인 콘텐츠 추출 → `state.document_full_text_map`에 캐싱

## 아키텍처 / 흐름도

Tool 실행 흐름과 상태 연동:

```
┌─────────────────────────────────────────────────────────────┐
│                      SearchTool                             │
│                                                             │
│  Agent → _execute()                                         │
│             │                                               │
│             ↓                                               │
│       Serper API 호출                                        │
│       (복수 쿼리 병렬)                                         │
│             │                                               │
│             ↓                                               │
│    SearchResult 생성                                         │
│             │                                               │
│             ↓                                               │
│  state.reference_documents에 저장                            │
│             │                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       FetchTool                             │
│                                                             │
│  Agent → _execute()                                         │
│             │                                               │
│             ↓                                               │
│      httpx HTTP 요청                                         │
│             │                                               │
│             ↓                                               │
│    BeautifulSoup 파싱                                        │
│             │                                               │
│       (메인 콘텐츠 추출)                                       │
│             │                                               │
│             ↓                                               │
│   state.document_full_text_map에 캐싱                        │
│             │                                               │
└─────────────────────────────────────────────────────────────┘
```

## 코드 읽기 순서

이 모듈을 처음 학습할 때는 다음 순서로 코드를 읽는 것을 권장합니다:

1. **`schemas.py`** - SearchResult와 ReferenceDocument 데이터 구조 이해
2. **`search.py`** - SearchTool 구현 (Serper API 연동, 병렬 검색)
3. **`fetch.py`** - FetchTool 구현 (웹페이지 추출, 콘텐츠 정제)
4. **`main.py`** - 두 도구의 통합 사용 데모

## 파일 구조

```
lec04_02_tools/
├── schemas.py    # SearchResult, ReferenceDocument 스키마
├── search.py     # SearchTool (Serper API 기반 웹 검색)
├── fetch.py      # FetchTool (웹페이지 콘텐츠 추출)
├── __init__.py   # 모듈 export
├── main.py       # 통합 데모
└── README.md     # 이 문서
```

## 각 파일의 역할

### `schemas.py` - 데이터 스키마

검색 결과와 참조 문서를 표현하는 Pydantic 모델:
- `SearchResult`: 검색 결과 (title, url, snippet)
- `ReferenceDocument`: 참조 문서 (title, url, snippet, content)

### `search.py` - SearchTool

Serper API를 사용하여 웹 검색을 수행합니다.

**핵심 기능:**
- `queries` 파라미터로 복수 쿼리를 동시에 검색 (병렬 실행)
- 검색 결과를 `state.reference_documents`에 자동 저장

### `fetch.py` - FetchTool

웹페이지에서 메인 콘텐츠를 추출합니다.

**핵심 기능:**
- httpx 비동기 HTTP 클라이언트로 웹페이지 요청
- BeautifulSoup으로 `<article>`, `<main>`, `role="main"` 등 메인 콘텐츠 영역 추출
- `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>` 등 불필요한 요소 제거
- 최대 콘텐츠 길이 제한 (50,000자) - 컨텍스트 윈도우 관리
- `state.document_full_text_map`에 추출한 콘텐츠 캐싱

## 이전 강의 대비 변경점

| 항목 | lec04_01 (BaseAgent) | lec04_02 (Common Tools) |
|------|---------------------|------------------------|
| Tool 유형 | CalculatorTool (예제) | SearchTool, FetchTool (실용 도구) |
| 외부 API | 없음 | Serper API, httpx |
| 상태 연동 | 단순 상태 | reference_documents, document_full_text_map |

## 사용 예제

```python
from lec04_01_base_agent.state import BaseAgentState
from lec04_02_tools import SearchTool, FetchTool, ReferenceDocument


class MyState(BaseAgentState):
    reference_documents: list[ReferenceDocument] = []
    document_full_text_map: dict[str, str] = {}


# SearchTool 사용
search_tool = SearchTool[MyState]()
result = await search_tool.call(
    state=state,
    tool_call_id="search_1",
    arguments={
        "queries": ["AI agent 2024", "LLM tool use"],
        "num_results": 5,
    },
)

# FetchTool 사용
fetch_tool = FetchTool[MyState]()
result = await fetch_tool.call(
    state=state,
    tool_call_id="fetch_1",
    arguments={"url": "https://example.com/article"},
)
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec04-02
```

실행 시 다음이 수행됩니다:
1. SearchTool로 웹 검색 실행 (복수 쿼리)
2. 검색 결과 출력
3. FetchTool로 검색 결과 중 첫 번째 URL의 콘텐츠 추출
4. 추출된 콘텐츠 미리보기

## 학습 포인트

1. **BaseTool 확장**: `_execute()` 메서드 구현, 파라미터 JSON Schema 정의
2. **상태 연동**: Tool 실행 결과를 Agent 상태에 자동 저장하는 패턴
3. **병렬 처리**: 복수 검색 쿼리를 `asyncio.gather`로 동시 실행

## 참고

- BaseTool 인터페이스: `lec04_01_base_agent/tool.py`

---

## 강의 내비게이션

← [이전 강의: lec04_01_base_agent](../lec04_01_base_agent/README.md) | [다음 강의: lec05_01_outliner](../lec05_01_outliner/README.md) →
