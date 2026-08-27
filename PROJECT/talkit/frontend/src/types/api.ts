// API 공통 에러/페이지네이션 관련 타입 정의
import type { UserMembership } from '@/types/membership'

export interface ApiErrorBody {
  error: string
  message?: string
  feature?: string
  // GET /me/membership이 404일 때, 과거에 만료된 멤버십이 있었다면 같이 내려준다
  // ("한 번도 결제 안 함"과 "만료됨"을 프론트에서 구분하기 위함).
  expired_membership?: UserMembership | null
}

export interface PaginationMeta {
  total: number
  page: number
  per_page: number
}
