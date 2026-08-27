import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useProfileQuery } from './useProfileQuery'
import { useUserStore } from '@/stores/userStore'
import { withQueryClient } from '@/test/test-utils'

const { getProfileMock } = vi.hoisted(() => ({ getProfileMock: vi.fn() }))

vi.mock('@/services/profileApi', () => ({
  profileApi: { getProfile: getProfileMock },
}))

describe('useProfileQuery', () => {
  beforeEach(() => {
    getProfileMock.mockReset()
    useUserStore.setState({ userId: null, adminToken: null })
  })

  it('userId가 없으면 쿼리가 비활성화되어 API를 호출하지 않는다', () => {
    const { result } = renderHook(() => useProfileQuery(), { wrapper: withQueryClient() })

    expect(result.current.fetchStatus).toBe('idle')
    expect(getProfileMock).not.toHaveBeenCalled()
  })

  it('userId가 있으면 profile 데이터를 반환한다', async () => {
    useUserStore.setState({ userId: 1 })
    const profile = { id: 1, email: 'a@b.com', name: '홍길동', phone_number: '010-1234-5678' }
    getProfileMock.mockResolvedValue(profile)

    const { result } = renderHook(() => useProfileQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(profile)
  })
})
