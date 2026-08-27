import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useMembershipQuery } from './useMembershipQuery'
import { useUserStore } from '@/stores/userStore'
import { ApiError } from '@/services/apiClient'
import { withQueryClient } from '@/test/test-utils'
import type { UserMembership } from '@/types/membership'

const { getMyMembershipMock } = vi.hoisted(() => ({ getMyMembershipMock: vi.fn() }))

vi.mock('@/services/membershipApi', () => ({
  membershipApi: { getMyMembership: getMyMembershipMock },
}))

const membership: UserMembership = {
  id: 1,
  plan: { id: 2, name: '프리미엄', features: ['learning', 'conversation'] },
  starts_at: '2026-06-01T00:00:00Z',
  expires_at: '2026-08-01T00:00:00Z',
  days_remaining: 42,
}

describe('useMembershipQuery', () => {
  beforeEach(() => {
    getMyMembershipMock.mockReset()
    useUserStore.setState({ userId: null, adminToken: null })
  })

  it('userId가 없으면 쿼리가 비활성화되어 API를 호출하지 않는다', () => {
    const { result } = renderHook(() => useMembershipQuery(), { wrapper: withQueryClient() })

    expect(result.current.fetchStatus).toBe('idle')
    expect(getMyMembershipMock).not.toHaveBeenCalled()
  })

  it('userId가 있으면 멤버십 데이터를 반환한다', async () => {
    useUserStore.setState({ userId: 1 })
    getMyMembershipMock.mockResolvedValue({ membership })

    const { result } = renderHook(() => useMembershipQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(membership)
  })

  it('404 ApiError는 에러가 아닌 null 데이터로 처리된다', async () => {
    useUserStore.setState({ userId: 1 })
    getMyMembershipMock.mockRejectedValue(new ApiError(404, { error: 'no_active_membership' }))

    const { result } = renderHook(() => useMembershipQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeNull()
    expect(result.current.isError).toBe(false)
  })

  it('404가 아닌 에러는 그대로 에러 상태로 전달된다', async () => {
    useUserStore.setState({ userId: 1 })
    getMyMembershipMock.mockRejectedValue(new ApiError(500, { error: 'server_error' }))

    const { result } = renderHook(() => useMembershipQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error).toBeInstanceOf(ApiError)
  })
})
