import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { usePlansQuery } from './usePlansQuery'
import { withQueryClient } from '@/test/test-utils'
import type { MembershipPlan } from '@/types/membership'

const { getPlansMock } = vi.hoisted(() => ({ getPlansMock: vi.fn() }))

vi.mock('@/services/membershipApi', () => ({
  membershipApi: { getPlans: getPlansMock },
}))

const plans: MembershipPlan[] = [
  {
    id: 1,
    name: '베이직',
    features: ['learning'],
    duration_days: 30,
    price_cents: 129_000,
    currency: 'KRW',
  },
]

describe('usePlansQuery', () => {
  beforeEach(() => {
    getPlansMock.mockReset()
  })

  it('plans 배열을 반환한다', async () => {
    getPlansMock.mockResolvedValue({ plans })

    const { result } = renderHook(() => usePlansQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(plans)
  })

  it('API 에러는 그대로 전파된다', async () => {
    getPlansMock.mockRejectedValue(new Error('network error'))

    const { result } = renderHook(() => usePlansQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
