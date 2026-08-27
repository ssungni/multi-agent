// 앱 전역에서 공유하는 상수 모음.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

// 멤버십 기능 코드 -> 화면에 표시할 한글 라벨 매핑.
export const FEATURE_LABELS: Record<string, string> = {
  learning: 'AI 표현 학습',
  conversation: 'AI 롤플레잉',
  analysis: '무제한 AI 분석',
}

// 결제 연동 없이 카드 등록/결제 흐름을 테스트하기 위한 모의(mock) 토큰 값들.
export const MOCK_CARD_TOKENS = {
  success: 'tok_mock_ok',
  fail: 'tok_mock_fail',
  expired: 'tok_mock_expired',
  stolen: 'tok_mock_stolen',
  limit: 'tok_mock_limit_reached',
} as const

// 멤버십 잔여일이 이 값 이하로 떨어지면 "곧 만료" 경고를 보여준다.
export const LOW_DAYS_THRESHOLD = 7

// AI 튜터/롤플레이 세션 시간 한도 — 도달하면 AI가 다음 응답에서 자연스럽게 마무리한다.
export const SESSION_HARD_LIMIT_MS = 30 * 60 * 1000

// getByteTimeDomainData 기준 발화 감지 임계값 — useAutoStopOnSilence(자동 턴 종료)와
// useSpeechWhileMuted(음소거 중 발화 안내)가 동일한 기준으로 판단하도록 공유한다.
export const VOICE_AMPLITUDE_THRESHOLD = 18
