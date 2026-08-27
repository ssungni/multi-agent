// 관리자용 사용자 목록 조회 및 멤버십 부여/회수를 담당하는 API 서비스
import { apiRequest } from '@/services/apiClient'
import type {
  AdminUsersResponse,
  GrantMembershipRequest,
  GrantMembershipResponse,
  RevokeMembershipResponse,
} from '@/types/admin'

export const adminApi = {
  // 관리자 권한으로 사용자 목록을 페이지 단위로 조회
  getUsers: (page = 1, adminToken?: string) =>
    apiRequest<AdminUsersResponse>(`/admin/users?page=${page}`, {}, { admin: true, adminToken }),

  // 관리자 권한으로 특정 사용자에게 멤버십을 부여
  grantMembership: (body: GrantMembershipRequest) =>
    apiRequest<GrantMembershipResponse>(
      '/admin/memberships',
      { method: 'POST', body: JSON.stringify(body) },
      { admin: true }
    ),

  // 관리자 권한으로 멤버십을 회수
  revokeMembership: (membershipId: number) =>
    apiRequest<RevokeMembershipResponse>(
      `/admin/memberships/${membershipId}`,
      { method: 'DELETE' },
      { admin: true }
    ),
}
