// 결제 요청/응답 관련 타입 정의
export interface PaymentRequest {
  membership_plan_id: number
  payment_method: 'card'
  card_token: string
}

export interface PaymentResponse {
  payment: {
    id: number
    status: string
    amount_cents: number
  }
  membership: {
    id: number
    expires_at: string
  }
}
