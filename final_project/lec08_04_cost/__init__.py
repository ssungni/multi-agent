"""비용/속도 최적화 (강의 08-04)

Claude API의 cache_control, 모델 전환, score 기반 평가를 활용하여
Agent 시스템의 비용과 속도를 최적화합니다.

주요 구성요소:
- cache_control.py: apply_cache_control_blocks 함수
- model_selector.py: 작업별 모델 선택 전략 (ModelSelector)
- evaluators.py: Score 기반 Evaluator (score에서 passed 도출)
- base.py: BaseAgent에 cache_control 통합
- main.py: 통합 최적화 데모 (Optimized sub-agent + evaluator 교체)
"""
