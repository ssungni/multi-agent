// 결제 생성 요청을 담당하는 API 서비스
import { apiRequest } from '@/services/apiClient'
import type { PaymentRequest, PaymentResponse } from '@/types/payment'

export const paymentApi = {
  // 결제 요청을 생성
  create: (body: PaymentRequest) =>
    apiRequest<PaymentResponse>('/payments', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
