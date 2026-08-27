# lec08_03_quality — 프롬프트 엔지니어링으로 퀄리티 개선

> Before/After 비교를 통해 프롬프트 엔지니어링 전략의 효과를 학습합니다.

## 개요

Agent의 출력 품질을 체계적으로 개선하는 전략과 도구를 제공하는 강의 모듈입니다.
기존 lec05의 Outliner/Evaluator를 개선 전(Baseline)으로 두고, 프롬프트 엔지니어링 전략을 적용한 개선 후(Improved) 버전을 비교하며 학습합니다.

## 핵심 개념

### 왜 필요한가
Agent의 출력 품질은 프롬프트에 크게 의존합니다.
동일한 Agent 구조에서도 **프롬프트 개선만으로** 출력 품질이 크게 향상될 수 있습니다.

### 무엇을 배우는가
세 가지 프롬프트 엔지니어링 전략을 학습합니다:
1. **Evaluation Criteria Injection**: 평가 기준을 생성 프롬프트에 주입
2. **Role & Persona Setting**: 구체적인 전문가 역할 부여

### 어떻게 동작하는가
1. Baseline 프롬프트(lec05 원본)와 Improved 프롬프트를 비교
2. 전략 함수를 Baseline에 적용하여 Improved를 동적 생성
3. EnhancedOutlineEvaluator로 루브릭 기반 세분화 평가

> **Note**: 이 모듈은 실행 데모(main.py)를 포함하지 않습니다. LLM 출력의 비결정성으로 인해 Before/After 데모가 매번 명확한 차이를 보여주기 어렵기 때문입니다. 대신 코드 모듈을 제공하고 강의에서 강사가 직접 설명합니다.

## 아키텍처 / 흐름도

```
BASELINE prompts (lec05 originals)
        ↓
Strategy Functions:
├── apply_evaluation_criteria_injection()
├── apply_role_persona_setting()
        ↓
IMPROVED prompts (dynamically generated)
        ↓
EnhancedOutlineEvaluator (rubric-based scoring)
```

## 코드 읽기 순서

이 강의를 이해하기 위한 권장 코드 읽기 순서:

1. **prompts.py**
   - `BASELINE_OUTLINER_SYSTEM_PROMPT` 먼저 읽기
   - 전략 함수 3개 순서대로 읽기:
     - `apply_evaluation_criteria_injection()`
     - `apply_role_persona_setting()`
   - `IMPROVED_OUTLINER_SYSTEM_PROMPT` 확인 (동적 생성 결과)
   - `BASELINE_EVALUATOR_PROMPT` vs `IMPROVED_EVALUATOR_PROMPT` 비교

2. **evaluator.py** - EnhancedOutlineEvaluator와 루브릭 기반 평가 구조 이해

## 학습 포인트

### 1. Comparison-Driven Learning (비교 기반 학습)
"이 전략이 좋다"라고 설명하는 것보다, 실제 프롬프트를 Before/After로 비교하는 것이 효과적입니다.
`prompts.py`에서 `BASELINE_*`과 `IMPROVED_*`를 나란히 비교하며 차이를 확인합니다.

### 2. Evaluation Criteria Injection (평가 기준 주입)
Agent가 Evaluator의 평가 기준을 모른 채 출력을 생성하면, 첫 생성에서 기준을 충족하지 못할 확률이 높습니다.
평가 기준을 시스템 프롬프트에 주입하면 첫 생성부터 기준을 의식한 출력을 만들어 feedback loop 반복 횟수를 줄입니다.

### 3. Role & Persona Setting (역할/페르소나 설정)
"You are an outline generator" (모호한 역할) 대신 "You are a senior research analyst with 10+ years of experience" (구체적 역할)을 설정하면, LLM이 해당 분야 전문가 수준의 어휘, 구조, 깊이로 응답합니다.

### 4. Step-by-Step Instruction (단계별 작업 지시)
"좋은 아웃라인을 만들어라"라는 암묵적 지시 대신, 구체적인 작업 단계를 나열하면 Agent가 체계적으로 작업을 수행합니다.

### 5. Rubric-Based Evaluation (루브릭 기반 평가)
자유 형식 평가 대신 기준별 1-5점 점수화, 구체적 예시 요구, 우선순위 피드백을 적용하면 평가의 일관성과 피드백의 실행 가능성이 향상됩니다.

## 코드 구조

```
lec08_03_quality/
├── __init__.py       # 모듈 소개 및 구성 설명
├── prompts.py        # 전략 함수 + Before/After 프롬프트 비교
├── evaluator.py      # 강화된 Evaluator (EnhancedOutlineEvaluator)
└── README.md         # 이 파일
```

### prompts.py - 전략 함수 + Before/After 프롬프트 비교

하나의 파일에서 전략과 그 적용 결과를 함께 보여줍니다:

| 구성 요소 | 설명 |
|-----------|------|
| `BASELINE_OUTLINER_SYSTEM_PROMPT` | 기존 Outliner 시스템 프롬프트 (lec05 원본) |
| `BASELINE_EVALUATOR_PROMPT` | 기존 Evaluator 프롬프트 (lec05 원본) |
| `apply_evaluation_criteria_injection()` | 전략 함수: 평가 기준 주입 |
| `apply_role_persona_setting()` | 전략 함수: 역할/페르소나 설정 |
| `apply_step_by_step_instruction()` | 전략 함수: 단계별 작업 지시 |
| `IMPROVED_OUTLINER_SYSTEM_PROMPT` | **동적 생성**: BASELINE에 3가지 전략을 적용한 결과 |
| `IMPROVED_EVALUATOR_PROMPT` | 개선된 Evaluator 프롬프트 (rubric + 우선순위 피드백) |

핵심: `IMPROVED_OUTLINER_SYSTEM_PROMPT`는 하드코딩이 아닌, 전략 함수를 BASELINE에 적용하여 동적으로 생성됩니다.

### evaluator.py - 강화된 Evaluator

기존 `OutlineEvaluator`를 상속하여 rubric 기반 세분화 평가를 수행하는 `EnhancedOutlineEvaluator`를 제공합니다:
- `CriterionScore`: 기준별 점수(1-5), 사유, 개선 제안
- `DetailedEvaluationResult`: 합격 여부, 전체 점수, 기준별 점수, 우선순위 피드백, 개선 예시
- `EnhancedOutlineEvaluator`: `IMPROVED_EVALUATOR_PROMPT`를 사용하는 강화된 Evaluator

## 강의 활용 가이드 (25분)

1. **Outliner 시스템 프롬프트 비교** (10분)
   - `BASELINE_OUTLINER_SYSTEM_PROMPT` 먼저 보여주기
   - "이 프롬프트의 문제점이 무엇인가?" 질문
   - 전략 함수 3가지 설명 → `IMPROVED_OUTLINER_SYSTEM_PROMPT` 동적 생성 과정 시연

2. **Evaluator 프롬프트 비교** (10분)
   - `BASELINE_EVALUATOR_PROMPT` 먼저 보여주기
   - `IMPROVED_EVALUATOR_PROMPT`를 보여주며 4가지 개선 전략 설명

3. **EnhancedOutlineEvaluator 코드 리뷰** (5분)
   - `DetailedEvaluationResult` 구조 설명
   - 기존 `EvaluationResult`와의 차이점 비교

## 의존성

```
lec08_03_quality 의존:
├── lec05_01_outliner  (OutlineEvaluator, prompts, schemas)
├── lec02_01_litellm   (router)
└── lec02_02_langfuse  (setup_langfuse)
```

---

## 강의 네비게이션

← [이전 강의: lec07_02_ask_user - AskUserQuestion HITL Tool](../lec07_02_ask_user/README.md) | [다음 강의: lec08_04_cost - 비용/속도 최적화 →](../lec08_04_cost/README.md)
