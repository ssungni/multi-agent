import { describe, it, expect, vi } from 'vitest'
import { paymentApi } from './paymentApi'
import type { PaymentRequest } from '@/types/payment'

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }))

vi.mock('@/services/apiClient', () => ({
  apiRequest: apiRequestMock,
}))

describe('paymentApi', () => {
  it('create는 POST /payments에 body를 JSON으로 직렬화해 전달한다', async () => {
    apiRequestMock.mockResolvedValue({ payment: {}, membership: {} })
    const body: PaymentRequest = {
      membership_plan_id: 1,
      payment_method: 'card',
      card_token: 'tok_mock_ok',
    }

    await paymentApi.create(body)

    expect(apiRequestMock).toHaveBeenCalledWith('/payments', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  })
})
