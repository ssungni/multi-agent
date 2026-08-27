import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useInterestsQuery } from './useInterestsQuery'
import { useUserStore } from '@/stores/userStore'
import { withQueryClient } from '@/test/test-utils'

const { getInterestsMock } = vi.hoisted(() => ({ getInterestsMock: vi.fn() }))

vi.mock('@/services/interestsApi', () => ({
  interestsApi: { getInterests: getInterestsMock },
}))

describe('useInterestsQuery', () => {
  beforeEach(() => {
    getInterestsMock.mockReset()
    useUserStore.setState({ userId: null, adminToken: null })
  })

  it('userId가 없으면 쿼리가 비활성화되어 API를 호출하지 않는다', () => {
    const { result } = renderHook(() => useInterestsQuery(), { wrapper: withQueryClient() })

    expect(result.current.fetchStatus).toBe('idle')
    expect(getInterestsMock).not.toHaveBeenCalled()
  })

  it('userId가 있으면 interests 배열을 반환한다', async () => {
    useUserStore.setState({ userId: 1 })
    getInterestsMock.mockResolvedValue({ interests: ['tutor_food', 'tutor_travel'] })

    const { result } = renderHook(() => useInterestsQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(['tutor_food', 'tutor_travel'])
  })
})
