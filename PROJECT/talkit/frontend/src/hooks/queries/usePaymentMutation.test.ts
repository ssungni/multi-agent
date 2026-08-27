import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { usePaymentMutation } from './usePaymentMutation'
import { useUserStore } from '@/stores/userStore'
import { createTestQueryClient, withQueryClient } from '@/test/test-utils'
import type { PaymentRequest } from '@/types/payment'

const { createMock } = vi.hoisted(() => ({ createMock: vi.fn() }))

vi.mock('@/services/paymentApi', () => ({
  paymentApi: { create: createMock },
}))

const body: PaymentRequest = {
  membership_plan_id: 2,
  payment_method: 'card',
  card_token: 'tok_mock_ok',
}

describe('usePaymentMutation', () => {
  beforeEach(() => {
    createMock.mockReset()
    useUserStore.setState({ userId: 1, adminToken: null })
  })

  it('결제 성공 시 membership 쿼리 캐시를 무효화한다', async () => {
    createMock.mockResolvedValue({ payment: {}, membership: {} })
    const queryClient = createTestQueryClient()
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => usePaymentMutation(), {
      wrapper: withQueryClient(queryClient),
    })

    await act(async () => {
      await result.current.mutateAsync(body)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['membership', 1] })
  })

  it('결제 실패 시 isError가 true가 된다', async () => {
    createMock.mockRejectedValue(new Error('payment_failed'))

    const { result } = renderHook(() => usePaymentMutation(), { wrapper: withQueryClient() })

    act(() => {
      result.current.mutate(body)
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
