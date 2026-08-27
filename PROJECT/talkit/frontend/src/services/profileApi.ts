// 사용자 프로필 조회를 담당하는 API 서비스
import { apiRequest } from '@/services/apiClient'
import type { Profile } from '@/types/profile'

export const profileApi = {
  // 현재 사용자의 프로필 정보를 조회
  getProfile: () => apiRequest<Profile>('/me/profile'),
}
