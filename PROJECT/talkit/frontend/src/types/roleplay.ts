// 롤플레이 시나리오 관련 타입 정의
export interface RoleplayScenario {
  id: number
  series_title: string
  title: string
  level: string
  description: string
  position: number
  topic_id: string
  // 연습 모드 힌트(opening) / 실전 모드 인캐릭터 대사(live_opening) — 백엔드
  // Ai::ChatService::TOPICS가 단일 진실 공급원이며, 여기서는 그 값을 그대로 받아온다.
  opening: string | null
  live_opening: string | null
}
