# lec08_04_cost — 비용/속도 최적화 (Cache Control + 모델 전환 + Score 기반 평가 + 검색 최적화)

> 다섯 가지 전략으로 Agent 시스템의 비용과 속도를 최적화합니다.

이 강의에서는 Agent 시스템의 비용과 속도를 최적화하는 다섯 가지 전략을 학습합니다.

## 개요

- **Cache Control**: Claude API의 캐시 기능을 활용하여 반복되는 컨텍스트의 비용을 90%까지 절감
- **모델 전환 (Model Selection)**: 작업 유형에 따라 적절한 모델 선택 (Evaluator -> 경량 모델)
- **Score 기반 Evaluator**: score에서 passed를 도출하여 soft pass 자동 적용 (lec08_03 패턴)
- **SearchAgent 파라미터 제한**: max_iterations, 쿼리 수, 결과 수 제한으로 검색 비용 절감
- **검색 결과 선별 전달**: LLM 기반 관련성 필터링으로 불필요한 토큰 전달 방지

## 핵심 개념

### 왜 필요한가
Multi-agent 시스템은 수십 번의 LLM 호출을 수행하므로 비용이 빠르게 증가합니다.
모든 작업에 동일한 고성능 모델을 사용하는 것은 비효율적입니다.

### 무엇을 배우는가
다섯 가지 비용 최적화 전략을 학습합니다:
1. **Cache Control**: 반복되는 컨텍스트의 입력 토큰 비용 90% 절감
2. **Model Selection**: Evaluator에 경량 모델 사용 (sonnet → haiku)
3. **Score 기반 Evaluator**: LLM에게 score + feedback만 요청, passed는 score >= 0.7로 도출
4. **SearchAgent 파라미터 제한**: max_iterations=7, 쿼리 최대 5개, 결과 20개로 제한
5. **검색 결과 선별 전달**: LLM(gpt-4.1-mini) 기반으로 관련 있는 검색 결과만 선별

### 어떻게 동작하는가
1. `_hook_pre_llm_call()`에서 `apply_cache_control_blocks()` 적용
2. `ModelSelector`로 작업 유형별 최적 모델 선택
3. Scored Evaluator가 score >= 0.7이면 `passed=True` 반환 → Tool 내부 평가 루프가 자동 종료
4. `FilteringSearchTool`로 쿼리/결과 수 제한 + 매 검색 호출마다 LLM 기반 관련성 필터링 → 필터된 결과만 history에 유지
5. Scored Evaluator를 도구 내부 evaluator에 주입하여 score 기반 평가 적용

## 아키텍처 / 흐름도

```
Optimized Agent:
├── Cache Control: system + last msg + last user → 90% input savings
├── Model Selection: Evaluator → claude-4.5-haiku (cheaper)
├── Score-based Evaluator: score → passed 도출 (soft pass 내장)
├── Adaptive max_iterations: 섹션 수 × 2 기반 동적 반복 제한
├── SearchAgent Limits: max_iterations=7, queries≤5, num_results=20
├── Result Filtering: FilteringSearchTool이 매 검색마다 LLM(gpt-4.1-mini) 필터링
└── Scored Evaluator: 도구 내부 evaluator를 score 반환 버전으로 교체
```

## 코드 읽기 순서

이 강의를 이해하기 위한 권장 코드 읽기 순서:

1. **cache_control.py** - Claude Cache Control 3블록 전략 이해
2. **model_selector.py** - TaskType별 모델 선택 로직 확인
3. **evaluators.py** - Score 기반 Evaluator (score에서 passed 도출) 패턴 이해
4. **search.py** - FilteringSearchTool(매 검색마다 필터링)과 filter_references_by_relevance 이해
5. **base.py** - BaseAgent에 cache_control이 통합되는 방식 확인
6. **main.py** - Optimized sub-agent 구성 및 도구 내부 evaluator 교체 패턴 확인

## 파일 구조

```
lec08_04_cost/
├── __init__.py          # 패키지 초기화
├── base.py              # BaseAgent 확장 (cache_control 통합)
├── cache_control.py     # Claude Cache Control 유틸리티
├── evaluators.py        # Score 기반 Evaluator (score에서 passed 도출)
├── model_selector.py    # 작업별 모델 선택 전략 (ModelSelector)
├── search.py            # FilteringSearchTool + filter_references_by_relevance
├── main.py              # 통합 최적화 데모 (Optimized sub-agent + evaluator 교체)
└── README.md            # 이 파일
```

## 이전 강의 대비 변경점

### lec06_02_hitl/base.py에서 확장된 부분

| 항목 | 변경 내용 |
|------|----------|
| `_hook_pre_llm_call()` | `apply_cache_control_blocks` 적용 |

### 신규 추가 파일

- `cache_control.py`: apply_cache_control_blocks 함수
- `model_selector.py`: TaskType enum, ModelConfig, ModelSelector 클래스
- `evaluators.py`: Score 기반 Evaluator — LLM에게 score + feedback만 요청, passed는 score >= 0.7로 도출 (lec08_03 패턴)
- `search.py`: FilteringSearchTool (검색 + 매 호출마다 자동 필터링), filter_references_by_relevance (LLM 기반 필터링)

### main.py 확장 내용

- 기존 `CacheOptimizedOrchestratorAgent` 클래스 보존
- `OptimizedOutlinerAgent`: GenerateOutlineTool 내부 evaluator를 ScoredOutlineEvaluator로 교체
- `OptimizedResearcherWorkflow`: Evaluator를 haiku로 변경, FilteringSearchTool로 검색 + 자동 필터링
- `OptimizedWriterAgent`: WriteSectionTool/PolishReportTool 내부 evaluator를 Scored 버전으로 교체, adaptive max_iterations
- `OptimizedOrchestratorAgent`: Optimized sub-agent 주입 + Cache Control
- `estimate_cost()`: 토큰 기반 비용 추정 유틸리티
- `run_optimized()`: Optimized 실행

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec08-04
```

### 데모 흐름

```
Optimized - OptimizedOrchestratorAgent (All Optimizations)
    - Evaluator에 claude-4.5-haiku 사용
    - Cache Control ON (3-block strategy)
    - Score-based Evaluator (score >= 0.7 → passed)
    - Adaptive max_iterations (섹션 수 기반)
    - SearchAgent: max_iterations=7, queries≤5, num_results=20
    - Result Filtering: ON (gpt-4.1-mini)
```

## 학습 포인트

1. **Claude Cache Control 전략**
   - 최대 4개의 cache_control 블록 활용 (이 강의에서는 3개 사용)
   - 시스템 프롬프트, 마지막 메시지, 마지막 사용자 메시지 캐싱
   - 캐시 히트 시 입력 토큰 비용 90% 절감
   - Note: lec08_05_context에서 compaction/summarization 구현 후 4번째 블록(축소 메시지) 추가

2. **모델 전환 (Model Selection)**
   - 작업 유형별 모델 매핑: Evaluator -> 경량 모델 (haiku)
   - 비용 비교:
     - claude-4.5-sonnet: $3/1M input, $15/1M output
     - claude-4.5-haiku: $0.80/1M input, $4/1M output
   - Evaluator는 구조화된 판단만 수행하므로 경량 모델로 충분
   - Constructor Injection 패턴으로 sub-agent 교체

3. **Score 기반 Evaluator (lec08_03 패턴)**
   - LLM에게 `score` + `feedback`만 요청 (`_ScoredEvalResponse`)
   - `passed = score >= 0.7`로 도출 → LLM이 passed/score를 독립 판단할 때의 불일치 방지
   - 반환 타입이 기존과 동일 (`EvaluationResult` 등) → Tool 내부 평가 루프 수정 불필요
   - Tool의 `if eval_result.passed: break`가 자동으로 soft pass 처리

4. **SearchAgent 파라미터 제한 + 검색 결과 자동 필터링**
   - `max_iterations`: 10 → 7로 제한하여 불필요한 검색 반복 방지
   - `FilteringSearchTool`: OptimizedSearchTool을 상속하여 매 `search_web` 호출마다 자동 필터링
     - 검색 실행 → 새로 추가된 문서만 `filter_references_by_relevance`로 필터
     - 필터된 결과만 `state.reference_documents`와 tool result(history)에 유지
     - 불필요한 토큰이 history에 쌓이지 않아 downstream 비용 절감
   - `filter_references_by_relevance`: 경량 모델(gpt-4.1-mini)로 title + snippet 기반 관련성 판단
   - 비용 비교: gpt-4.1-mini $0.4/1M input, $1.6/1M output

5. **캐시 최적화 설계**
   - 반복되는 컨텍스트를 캐시 블록 위치에 배치
   - 메시지 구조 설계 시 캐시 히트율 고려

## 비용 추적

비용 추적은 Langfuse UI에서 확인할 수 있습니다. Langfuse는 LLM 호출의 토큰 사용량, 비용, latency 등을 자동으로 추적합니다.

또한, `estimate_cost()` 함수를 사용하여 토큰 기반 비용을 프로그래밍 방식으로 추정할 수 있습니다:

```python
from lec08_04_cost.main import estimate_cost

# claude-4.5-sonnet으로 10K input + 2K output
cost_sonnet = estimate_cost("claude-4.5-sonnet", input_tokens=10000, output_tokens=2000)
# => $0.06

# claude-4.5-haiku로 동일 토큰
cost_haiku = estimate_cost("claude-4.5-haiku", input_tokens=10000, output_tokens=2000)
# => $0.016
```

---

## 강의 네비게이션

← [이전 강의: lec08_03_quality - Agent 퀄리티 개선](../lec08_03_quality/README.md) | [다음 강의: lec08_05_context - Context Engineering →](../lec08_05_context/README.md)
