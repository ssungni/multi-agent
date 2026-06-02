"""Agent 출력 품질 개선 - 프롬프트 엔지니어링 전략과 Before/After 비교.

이 모듈은 Agent의 출력 품질을 개선하기 위한 프롬프트 전략과,
그 전략을 적용한 전/후 프롬프트를 함께 제공합니다.

구성:
    1. BASELINE 프롬프트: lec05_01_outliner에서 사용한 원본
    2. 전략 함수 3가지: 프롬프트를 변환하는 유틸리티
    3. IMPROVED 프롬프트: 전략 함수를 BASELINE에 적용하여 **동적 생성**한 결과

핵심 아이디어 - Evaluation Criteria Injection:
    OutlinerAgent는 아웃라인을 생성한 뒤, OutlineEvaluator가 Coverage/Structure/
    Specificity 등 6개 기준으로 평가합니다. 문제는 Agent가 이 기준을 **모른 채**
    아웃라인을 생성한다는 것입니다.

    이 전략은 Evaluator의 평가 기준을 Agent의 시스템 프롬프트에 미리 주입하여,
    Agent가 "자신이 어떤 기준으로 평가될지" 알게 합니다. 결과적으로 첫 생성부터
    평가 기준을 의식한 출력을 만들어 feedback loop 반복 횟수를 줄입니다.

적용 예시::

    >>> from lec08_03_quality.prompts import (
    ...     BASELINE_OUTLINER_SYSTEM_PROMPT,
    ...     IMPROVED_OUTLINER_SYSTEM_PROMPT,
    ...     apply_role_persona_setting,
    ...     apply_evaluation_criteria_injection,
    ...     apply_step_by_step_instruction,
    ... )
    >>> # IMPROVED는 BASELINE에 전략 함수를 적용한 결과
    >>> len(IMPROVED_OUTLINER_SYSTEM_PROMPT) > len(BASELINE_OUTLINER_SYSTEM_PROMPT)
    True
"""

from __future__ import annotations

# ============================================================================
# 1. BASELINE 프롬프트 (lec05_01_outliner/prompts.py 원본)
# ============================================================================

# ---------------------------------------------------------------------------
# BASELINE Outliner 시스템 프롬프트
# ---------------------------------------------------------------------------
# 특징:
#   - "outline generation agent"라는 모호한 역할 설정
#   - Quality Criteria가 있지만, Evaluator의 평가 기준과 연결되지 않음
#   - Agent가 "어떤 기준으로 평가될지" 모름

BASELINE_OUTLINER_SYSTEM_PROMPT = """You are an outline generation agent. Your goal is to produce a structured, well-researched report outline on the user's topic through web research.

## Quality Criteria

- 3-7 main sections with logical flow (introduction → body → conclusion)
- Each section has a specific description (2-4 sentences with concrete points, no vague statements)
- No overlap between sections; balanced scope across sections

## Principles

- Base your outline on search results, not prior knowledge alone. If information is insufficient, search more.
- When the Evaluator returns feedback, address it and regenerate the outline.
- Finalize only after evaluation passes."""

# ---------------------------------------------------------------------------
# BASELINE Evaluator 프롬프트
# ---------------------------------------------------------------------------
# 특징:
#   - 6가지 기준으로 평가하지만 합격/불합격 기준이 불명확
#   - 피드백이 구조화되지 않음 (자유 형식)
#   - 구체적 개선 예시를 요구하지 않음
#   - 우선순위 없이 모든 피드백이 동등하게 제시됨

BASELINE_EVALUATOR_PROMPT = """You are evaluating an outline for a report on: {topic}

Outline to evaluate:
{outline_json}

Evaluate the outline on these criteria:

1. **Coverage**: Does it cover all important aspects of the topic?
   - Are major themes and perspectives included?
   - Are there obvious gaps or missing aspects?
   - Does it progress from introduction to conclusion?

2. **Structure**: Is the logical flow from introduction to conclusion clear?
   - Does each section naturally lead to the next?
   - Is there a coherent narrative arc?
   - Are sections organized in a sensible order?

3. **Specificity**: Are section descriptions specific enough to guide research?
   - Do descriptions contain concrete points rather than vague statements?
   - Would a researcher know what information to gather based on the description?
   - Are descriptions substantive (2-4 sentences with clear guidance)?

4. **Balance**: Are sections appropriately balanced in scope?
   - Are sections roughly comparable in breadth and depth?
   - Is any section too narrow or too broad relative to others?
   - Are there 3-7 main sections (not too few, not too many)?

5. **Relevance**: Is every section directly related to the topic?
   - Do all sections address the user's stated topic?
   - Are there any tangential or off-topic sections?

6. **Uniqueness**: Are sections distinct without overlap?
   - Does each section cover a unique aspect?
   - Is there content duplication between sections?"""


# ============================================================================
# 2. 프롬프트 엔지니어링 전략 (함수 + 데이터)
# ============================================================================

# ---------------------------------------------------------------------------
# 전략 데이터: Evaluator 평가 기준, 역할/페르소나, 작업 단계
# ---------------------------------------------------------------------------

# OutlineEvaluator가 사용하는 6가지 평가 기준.
# lec05_01_outliner/prompts.py의 EVALUATOR_PROMPT에 정의된 기준과 동일합니다.
# 시스템 프롬프트에 주입하면 Agent가 평가 기준을 미리 인지합니다.
OUTLINE_EVALUATION_CRITERIA: list[str] = [
    "Coverage: 주제의 모든 중요한 측면을 다루고 있는가? 주요 테마와 관점이 포함되어 있는가?",
    "Structure: 서론에서 결론까지의 논리적 흐름이 명확한가? 각 섹션이 자연스럽게 연결되는가?",
    "Specificity: 섹션 설명이 리서치를 안내할 만큼 구체적인가? 모호한 표현 대신 구체적 포인트가 있는가?",
    "Balance: 섹션 간 범위와 깊이가 균형 잡혀 있는가? 3-7개의 메인 섹션이 있는가?",
    "Relevance: 모든 섹션이 주제와 직접 관련되는가? 주제에서 벗어난 섹션이 없는가?",
    "Uniqueness: 섹션 간 내용 중복이 없는가? 각 섹션이 고유한 측면을 다루는가?",
]

# OutlinerAgent에 적합한 역할.
# 기존 "You are an outline generation agent" (모호한 역할)을 대체합니다.
# 구체적인 직무를 명시하면 LLM이 전문가 수준의 어휘와 깊이로 응답합니다.
OUTLINER_ROLE = "senior research analyst with 10+ years of experience in report writing"

# OutlinerAgent의 전문 분야 목록
OUTLINER_EXPERTISE: list[str] = [
    "comprehensive topic analysis",
    "structured report outlining",
    "identifying key themes from diverse sources",
]

# OutlinerAgent의 응답 톤
OUTLINER_TONE = "professional and analytical"


# ---------------------------------------------------------------------------
# 전략 함수 1: Evaluation Criteria Injection
# ---------------------------------------------------------------------------


def apply_evaluation_criteria_injection(
    system_prompt: str,
    criteria: list[str],
) -> str:
    """평가 기준을 시스템 프롬프트에 주입합니다.

    Agent가 자신의 출력이 어떤 기준으로 평가될지 미리 알게 하여
    자가 검증을 유도합니다.

    이 전략이 효과적인 이유:
        - Agent는 기본적으로 Evaluator의 기준을 모릅니다
        - 기준을 주입하면 첫 생성부터 기준을 의식한 출력을 만듭니다
        - 결과적으로 evaluation fail → feedback → regeneration 반복이 줄어듭니다

    Args:
        system_prompt: 기존 시스템 프롬프트
        criteria: 평가 기준 목록. OUTLINE_EVALUATION_CRITERIA를 사용하거나,
                  커스텀 기준을 전달할 수 있습니다.

    Returns:
        평가 기준이 주입된 시스템 프롬프트

    Examples:
        기존 OutlinerAgent 프롬프트에 평가 기준 주입::

            >>> from lec08_03_quality.prompts import (
            ...     BASELINE_OUTLINER_SYSTEM_PROMPT,
            ...     OUTLINE_EVALUATION_CRITERIA,
            ...     apply_evaluation_criteria_injection,
            ... )
            >>> result = apply_evaluation_criteria_injection(
            ...     BASELINE_OUTLINER_SYSTEM_PROMPT, OUTLINE_EVALUATION_CRITERIA
            ... )
            >>> "Coverage" in result
            True

        빈 기준 리스트는 원본을 그대로 반환::

            >>> result = apply_evaluation_criteria_injection("base prompt", [])
            >>> result
            'base prompt'
    """
    if not criteria:
        return system_prompt

    criteria_text = "\n".join(f"  - {criterion}" for criterion in criteria)

    injection_block = (
        "\n\n"
        "## Evaluation Criteria\n"
        "\n"
        "Your output will be evaluated against the following criteria.\n"
        "Before finalizing your response, perform a self-check against each criterion:\n"
        "\n"
        f"{criteria_text}\n"
        "\n"
        "For each criterion, verify that your output adequately addresses it.\n"
        "If any criterion is not met, revise your output before responding."
    )

    return system_prompt + injection_block


# ---------------------------------------------------------------------------
# 전략 함수 2: Role & Persona Setting
# ---------------------------------------------------------------------------


def apply_role_persona_setting(
    system_prompt: str,
    role: str,
    expertise: list[str] | None = None,
    tone: str | None = None,
) -> str:
    """역할/페르소나 설정을 프롬프트에 적용합니다.

    구체적인 역할(Role)과 전문성(Expertise)을 프롬프트 앞부분에
    설정하여 Agent의 출력 품질과 일관성을 향상시킵니다.

    이 전략이 효과적인 이유:
        - "You are an outline generator" (모호) vs
          "You are a senior research analyst with 10+ years of experience" (구체적)
        - 구체적 역할은 LLM이 해당 분야 전문가의 어휘, 구조, 깊이로 응답하게 만듭니다
        - expertise를 명시하면 출력의 초점이 명확해집니다

    Args:
        system_prompt: 기존 시스템 프롬프트
        role: 역할 명칭 (예: "senior research analyst with 10+ years of experience")
        expertise: 전문 분야 목록. None이면 전문 분야 섹션을 생략합니다.
        tone: 응답 톤 (예: "professional and analytical"). None이면 생략합니다.

    Returns:
        역할/페르소나가 설정된 시스템 프롬프트

    Examples:
        기존 OutlinerAgent 프롬프트의 역할을 강화::

            >>> result = apply_role_persona_setting(
            ...     system_prompt="You are an outline generator.",
            ...     role="senior research analyst with 10+ years of experience",
            ...     expertise=["structured report writing", "comprehensive topic analysis"],
            ...     tone="professional and analytical",
            ... )
            >>> result.startswith("You are a senior research analyst")
            True
    """
    persona_parts: list[str] = []

    persona_parts.append(f"You are a {role}.")

    if expertise:
        expertise_text = ", ".join(expertise)
        persona_parts.append(f"Your areas of expertise include: {expertise_text}.")

    if tone:
        persona_parts.append(f"Maintain a {tone} tone throughout your responses.")

    persona_block = " ".join(persona_parts)

    return f"{persona_block}\n\n{system_prompt}"


# ============================================================================
# 3. IMPROVED 프롬프트 (전략을 BASELINE에 적용하여 동적 생성)
# ============================================================================

# ---------------------------------------------------------------------------
# IMPROVED Outliner 시스템 프롬프트
# ---------------------------------------------------------------------------
# BASELINE에 2가지 전략을 순서대로 적용한 결과입니다.
# 아래 코드로 동일한 결과를 재현할 수 있습니다:
#
#   improved = apply_role_persona_setting(
#       BASELINE_OUTLINER_SYSTEM_PROMPT,
#       role=OUTLINER_ROLE, expertise=OUTLINER_EXPERTISE, tone=OUTLINER_TONE,
#   )
#   improved = apply_evaluation_criteria_injection(improved, OUTLINE_EVALUATION_CRITERIA)
#
# 적용된 전략:
#   [전략 1] Role & Persona Setting
#     - Before: "You are an outline generation agent" (모호)
#     - After: "You are a senior research analyst with 10+ years of experience" (구체적)
#
#   [전략 2] Evaluation Criteria Injection
#     - Before: Agent가 Evaluator의 평가 기준을 모른 채 생성
#     - After: 6가지 평가 기준을 시스템 프롬프트에 주입 → 자가 검증 유도

IMPROVED_OUTLINER_SYSTEM_PROMPT = """You are a senior research analyst with 10+ years of experience in report writing. Your areas of expertise include: comprehensive topic analysis, structured report outlining, identifying key themes from diverse sources. Maintain a professional and analytical tone throughout your responses.

You are an outline generation agent. Your goal is to produce a structured, well-researched report outline on the user's topic through web research.

## Quality Criteria

- 3-7 main sections with logical flow (introduction → body → conclusion)
- Each section has a specific description (2-4 sentences with concrete points, no vague statements)
- No overlap between sections; balanced scope across sections

## Principles

- Base your outline on search results, not prior knowledge alone. If information is insufficient, search more.
- When the Evaluator returns feedback, address it and regenerate the outline.
- Finalize only after evaluation passes.

## Evaluation Criteria

Your output will be evaluated against the following criteria.
Before finalizing your response, perform a self-check against each criterion:

  - Coverage: 주제의 모든 중요한 측면을 다루고 있는가? 주요 테마와 관점이 포함되어 있는가?
  - Structure: 서론에서 결론까지의 논리적 흐름이 명확한가? 각 섹션이 자연스럽게 연결되는가?
  - Specificity: 섹션 설명이 리서치를 안내할 만큼 구체적인가? 모호한 표현 대신 구체적 포인트가 있는가?
  - Balance: 섹션 간 범위와 깊이가 균형 잡혀 있는가? 3-7개의 메인 섹션이 있는가?
  - Relevance: 모든 섹션이 주제와 직접 관련되는가? 주제에서 벗어난 섹션이 없는가?
  - Uniqueness: 섹션 간 내용 중복이 없는가? 각 섹션이 고유한 측면을 다루는가?

For each criterion, verify that your output adequately addresses it.
If any criterion is not met, revise your output before responding."""

# ---------------------------------------------------------------------------
# IMPROVED Evaluator 프롬프트
# ---------------------------------------------------------------------------
# Outliner 프롬프트는 전략 함수로 BASELINE을 변환한 것이지만,
# Evaluator 프롬프트는 평가 방식 자체를 재설계한 것입니다.
#
# 적용된 개선:
#   [개선 1] Rubric-Based Scoring: 기준별 1-5점 점수화, 각 점수대의 의미를 정의
#   [개선 2] Score Examples: 각 기준에 대해 5점/2점 예시를 제시
#   [개선 3] Prioritized Feedback: 가장 영향이 큰 개선 사항을 우선순위대로 정렬
#   [개선 4] Improvement Examples: 구체적이고 실행 가능한 개선 예시
#   [개선 5] Clear Threshold: overall_score >= 0.7, 기준별 최소 2점

IMPROVED_EVALUATOR_PROMPT = """You are a senior editor reviewing an outline for a report on: {topic}

Outline to evaluate:
{outline_json}

## Evaluation Instructions

Evaluate the outline using the rubric below. For each criterion, assign a score from 1-5 and provide specific feedback.

### Scoring Rubric

For each criterion, use this scale:
- **5 (Excellent)**: Fully meets the criterion with no improvements needed
- **4 (Good)**: Mostly meets the criterion with minor improvements possible
- **3 (Acceptable)**: Meets the criterion at a basic level but has clear room for improvement
- **2 (Needs Work)**: Partially meets the criterion with significant gaps
- **1 (Poor)**: Does not meet the criterion

### Criteria

1. **Coverage** (주제 포괄성)
   - Are all important aspects of the topic covered?
   - Are major themes, perspectives, and sub-topics included?
   - Does it progress from introduction through body to conclusion?
   - *Score 5 example*: All key facets addressed, no obvious gaps, multiple perspectives included
   - *Score 2 example*: Major aspects missing, only surface-level themes covered

2. **Structure** (구조적 논리성)
   - Is the logical flow from introduction to conclusion clear?
   - Does each section naturally lead to the next?
   - Is there a coherent narrative arc throughout?
   - *Score 5 example*: Clear progression, smooth transitions, compelling narrative structure
   - *Score 2 example*: Sections feel disconnected, no clear narrative thread

3. **Specificity** (섹션 설명의 구체성)
   - Are section descriptions specific enough to guide detailed research?
   - Do descriptions contain concrete points rather than vague statements?
   - Are descriptions substantive (2-4 sentences with clear guidance)?
   - *Score 5 example*: Each description names specific data points, frameworks, or angles to investigate
   - *Score 2 example*: Descriptions are one-liners with generic phrases like "discuss various aspects"

4. **Balance** (섹션 간 균형)
   - Are sections roughly comparable in breadth and depth?
   - Is any section disproportionately narrow or broad?
   - Are there 3-7 main sections (not too few, not too many)?
   - *Score 5 example*: All sections have similar scope, none dominates or feels underweight
   - *Score 2 example*: One section covers everything while others are trivially narrow

5. **Relevance** (주제 관련성)
   - Is every section directly related to the stated topic?
   - Are there any tangential or off-topic sections?
   - *Score 5 example*: Every section clearly contributes to understanding the topic
   - *Score 2 example*: Some sections address loosely related or unrelated subjects

6. **Uniqueness** (섹션 간 중복 없음)
   - Does each section cover a unique aspect without overlap?
   - Is there content duplication between sections?
   - *Score 5 example*: Clear boundaries between sections, no repeated content
   - *Score 2 example*: Multiple sections cover the same ground from slightly different angles

## Output Requirements

Provide your evaluation in the following structured format:

1. **Criterion Scores**: For each of the 6 criteria, provide:
   - Score (1-5)
   - Brief reason for the score (1-2 sentences)

2. **Prioritized Feedback**: List the top 3 most impactful improvements, ordered by priority.
   - Each item should be actionable and specific
   - Focus on changes that would have the largest positive impact on quality"""
