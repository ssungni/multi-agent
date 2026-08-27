import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useExpiredMembershipQuery } from './useExpiredMembershipQuery'
import { useUserStore } from '@/stores/userStore'
import { ApiError } from '@/services/apiClient'
import { withQueryClient } from '@/test/test-utils'
import type { UserMembership } from '@/types/membership'

const { getMyMembershipMock } = vi.hoisted(() => ({ getMyMembershipMock: vi.fn() }))

vi.mock('@/services/membershipApi', () => ({
  membershipApi: { getMyMembership: getMyMembershipMock },
}))

const expiredMembership: UserMembership = {
  id: 6,
  plan: { id: 2, name: 'Premium', features: ['learning', 'conversation', 'analysis'] },
  starts_at: '2026-04-20T00:00:00Z',
  expires_at: '2026-06-19T00:00:00Z',
  days_remaining: 0,
}

describe('useExpiredMembershipQuery', () => {
  beforeEach(() => {
    getMyMembershipMock.mockReset()
    useUserStore.setState({ userId: null, adminToken: null })
  })

  it('userId가 없으면 쿼리가 비활성화되어 API를 호출하지 않는다', () => {
    const { result } = renderHook(() => useExpiredMembershipQuery(), { wrapper: withQueryClient() })

    expect(result.current.fetchStatus).toBe('idle')
    expect(getMyMembershipMock).not.toHaveBeenCalled()
  })

  it('활성 멤버십이 있으면 null을 반환한다 (보여줄 필요 없음)', async () => {
    useUserStore.setState({ userId: 1 })
    getMyMembershipMock.mockResolvedValue({
      membership: { id: 1, plan: { id: 2, name: 'Premium', features: [] }, starts_at: '', expires_at: '', days_remaining: 10 },
    })

    const { result } = renderHook(() => useExpiredMembershipQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeNull()
  })

  it('404이고 expired_membership이 있으면 그 정보를 반환한다 (만료됨 표시용)', async () => {
    useUserStore.setState({ userId: 1 })
    getMyMembershipMock.mockRejectedValue(
      new ApiError(404, { error: 'no_active_membership', expired_membership: expiredMembership })
    )

    const { result } = renderHook(() => useExpiredMembershipQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(expiredMembership)
  })

  it('404이고 expired_membership이 없으면 null을 반환한다 (한 번도 결제 안 함)', async () => {
    useUserStore.setState({ userId: 1 })
    getMyMembershipMock.mockRejectedValue(
      new ApiError(404, { error: 'no_active_membership', expired_membership: null })
    )

    const { result } = renderHook(() => useExpiredMembershipQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeNull()
  })

  it('404가 아닌 다른 에러는 그대로 에러 상태로 전달된다', async () => {
    useUserStore.setState({ userId: 1 })
    getMyMembershipMock.mockRejectedValue(new ApiError(500, { error: 'server_error' }))

    const { result } = renderHook(() => useExpiredMembershipQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
