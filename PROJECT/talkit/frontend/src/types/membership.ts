// 멤버십 플랜/구독 관련 타입 정의
export type MembershipFeature = 'learning' | 'conversation' | 'analysis'

export interface MembershipPlan {
  id: number
  name: string
  features: MembershipFeature[]
  duration_days: number
  price_cents: number
  currency: string
}

export interface UserMembership {
  id: number
  plan: Pick<MembershipPlan, 'id' | 'name' | 'features'>
  starts_at: string
  expires_at: string
  days_remaining: number
}
