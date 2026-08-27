// 롤플레이 시나리오 목록 조회를 담당하는 API 서비스
import { apiRequest } from '@/services/apiClient'
import type { RoleplayScenario } from '@/types/roleplay'

export const roleplayApi = {
  // 전체 롤플레이 시나리오 목록을 조회
  getScenarios: () => apiRequest<{ roleplay_scenarios: RoleplayScenario[] }>('/roleplay_scenarios'),
}
