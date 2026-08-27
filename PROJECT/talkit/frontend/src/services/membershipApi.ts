// 멤버십 플랜 조회 및 내 멤버십 정보 조회를 담당하는 API 서비스
import { apiRequest } from '@/services/apiClient'
import type { MembershipPlan, UserMembership } from '@/types/membership'

export const membershipApi = {
  // 사용 가능한 멤버십 플랜 목록을 조회
  getPlans: () =>
    apiRequest<{ plans: MembershipPlan[] }>('/membership_plans'),

  // 현재 로그인한 사용자의 멤버십 정보를 조회
  getMyMembership: () =>
    apiRequest<{ membership: UserMembership }>('/me/membership'),
}
