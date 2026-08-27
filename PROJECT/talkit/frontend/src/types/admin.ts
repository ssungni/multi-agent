// 관리자용 사용자/멤버십 관리 관련 타입 정의
export interface AdminUserMembership {
  id: number
  plan_name: string
  expires_at: string
}

export interface AdminUser {
  id: number
  email: string
  name: string
  active_membership: AdminUserMembership | null
  // 활성 멤버십이 없을 때만 채워진다 — "한 번도 결제 안 함"과 "만료됨"을 구분하기 위함.
  expired_membership: AdminUserMembership | null
}

export interface AdminUsersResponse {
  users: AdminUser[]
  meta: { total: number; page: number; per_page: number }
}

export interface GrantMembershipRequest {
  user_id: number
  membership_plan_id: number
  starts_at?: string
}

export interface GrantMembershipResponse {
  membership: {
    id: number
    user_id: number
    granted_by: string
    starts_at: string
    expires_at: string
    days_remaining: number
    replaced: boolean
    plan: { id: number; name: string; features: string[]; duration_days: number }
  }
}

export interface RevokeMembershipResponse {
  message: string
}
