// 사용자 관심사 조회 및 수정을 담당하는 API 서비스
import { apiRequest } from '@/services/apiClient'
import type { InterestsResponse } from '@/types/interests'

export const interestsApi = {
  // 현재 사용자의 관심사 목록을 조회
  getInterests: () => apiRequest<InterestsResponse>('/me/interests'),

  // 현재 사용자의 관심사 목록을 갱신
  updateInterests: (interests: string[]) =>
    apiRequest<InterestsResponse>('/me/interests', {
      method: 'PUT',
      body: JSON.stringify({ interests }),
    }),
}
