# lec08_05_02_context — Context Engineering (2단계 압축 전략)

> Compaction + Summarization으로 컨텍스트 크기를 관리하고, Cache Control과 결합하여 비용을 최적화합니다.

이 강의에서는 Context Engineering을 통해 LLM의 컨텍스트 윈도우를 효율적으로 관리하는 방법을 학습합니다.

## 개요

Multi-agent 시스템에서 대화가 길어지면 컨텍스트가 수십만 토큰에 도달할 수 있습니다. 이를 해결하기 위해 2단계 압축 전략을 사용합니다:

## 핵심 개념

### 왜 필요한가
Multi-agent 시스템에서 대화가 길어지면 컨텍스트가 수십만 토큰에 도달합니다.
컨텍스트 윈도우를 초과하면 LLM 호출이 실패하고, 토큰이 많으면 비용이 급증합니다.

### 무엇을 배우는가
**2단계 점진적 압축 전략**을 학습합니다:
- Stage 1 (Compaction): 오래된 도구 결과를 ID만으로 압축
- Stage 2 (Summarization): 그래도 크면 오래된 대화를 요약

### 어떻게 동작하는가
1. `_hook_pre_llm_call()`에서 ContextManager.process() 호출
2. 128K 초과 → Compaction 실행 (도구 결과 → ID만 보존)
3. 100K 초과 → Summarization 실행 (오래된 대화 → 요약)
4. `apply_cache_control_blocks()`로 4개 캐시 블록 적용

---

1. **Compaction (Stage 1)**: 도구 결과를 압축하여 핵심 ID만 보존
2. **Summarization (Stage 2)**: Compaction으로도 부족하면 오래된 대화를 요약
3. **Cache Control**: 4개 블록 전략으로 반복되는 컨텍스트 비용 90% 절감

이 전략을 통해 다음을 달성합니다:
- 컨텍스트 크기를 128K 이하로 유지
- 토큰 비용 최적화 (압축 + 캐싱)
- 중요한 정보 손실 없이 대화 이력 관리

## 아키텍처 / 흐름도

```
Messages (200K tokens)
        ↓
Stage 1: Compaction (compact old tool results → IDs only)
        ↓
~130K tokens
        ↓
Stage 2: Summarization (summarize old conversation)
        ↓
~80K tokens
        ↓
Cache Control (4 blocks)
        ↓
LLM Call (optimized context)
```

## 상속 체인

```
OrchestratorAgent (lec06_01)
└── OptimizedOrchestratorAgent (lec08_04)
    └── ContextManagedOrchestratorAgent (this module)
```

## 코드 읽기 순서

이 강의를 이해하기 위한 권장 코드 읽기 순서:

1. **calculate_size.py** - 컨텍스트 크기 계산 방법 이해
2. **compaction.py** - Stage 1 도구 결과 압축 로직
3. **tool.py**
4. **summarization.py** - Stage 2 오래된 대화 요약 로직
5. **manager.py** - ContextManager의 2단계 압축 오케스트레이션
6. **cache_control.py** - 4블록 캐시 전략 (lec08_04에서 확장)
7. **base.py** - BaseAgent에 ContextManager가 통합되는 방식
8. **main.py** - 전체 통합 데모 실행 흐름

## 파일 구조

```
lec08_05_02_context/
├── __init__.py          # 패키지 초기화
├── manager.py           # ContextManager (2단계 압축 오케스트레이션)
├── compaction.py        # Stage 1: 도구 결과 압축
├── summarization.py     # Stage 2: 오래된 대화 요약
├── cache_control.py     # 4개 블록 캐시 제어 전략
├── calculate_size.py    # 컨텍스트 크기 계산 유틸리티
├── tool.py              # BaseTool with compact_result 메서드
├── base.py              # BaseAgent with ContextManager 통합
├── main.py              # 통합 실행 예제
└── README.md            # 이 문서
```

## 실행 방법

> 사전 준비: 루트 [README.md](../README.md)의 "개발 환경 셋업" 섹션을 참고하여 환경을 설정하세요.

```bash
rye run lec08-05-02
```

## 학습 포인트

### 1. 점진적 압축 전략

컨텍스트 관리는 단계적으로 진행됩니다:
- **Level 0**: 원본 유지 (< 128K)
- **Level 1**: Compaction만 적용 (128K ~ 100K)
- **Level 2**: Compaction + Summarization (> 100K)

이를 통해 필요한 만큼만 압축하여 정보 손실을 최소화합니다.

### 2. 복원 가능한 압축

ID 중심 압축으로 필요시 재검색이 가능합니다:
```python
# 압축된 결과
"[Compacted] Found papers: corpus:12345678, corpus:87654321"

# 필요시 재검색
search_papers(query=original_query)  # 원본 인자로 재호출
```

### 3. Cache Control과의 시너지

압축된 메시지도 캐싱하여 이중 최적화:
- Compaction: 토큰 수 감소 (비용 직접 절감)
- Cache Control: 반복 사용 시 90% 절감
- 결합 효과: 첫 호출 후 95%+ 비용 절감

### 4. Tool-Call Pair 보존

Summarization 시 도구 호출/응답 쌍을 보존하여:
- LLM이 도구 실행 컨텍스트를 이해 가능
- 도구 호출 결과를 참조할 수 있도록 보장

## 참고 자료

- **OptimizedOrchestratorAgent**: `lecture/lec08_04_cost/main.py`
- **BaseAgent with Context**: `lecture/lec08_05_02_context/base.py`
- **ContextManager**: `lecture/lec08_05_02_context/manager.py`
- **Compaction**: `lecture/lec08_05_02_context/compaction.py`
- **Summarization**: `lecture/lec08_05_02_context/summarization.py`
- **Cache Control**: `lecture/lec08_05_02_context/cache_control.py`

---

## 강의 네비게이션

← [이전 강의: lec08_05_01_file_comm - File-based Communication](../lec08_05_01_file_comm/README.md) | (마지막 강의)
