import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useAdminUsersQuery } from './useAdminUsersQuery'
import { useUserStore } from '@/stores/userStore'
import { withQueryClient } from '@/test/test-utils'

const { getUsersMock } = vi.hoisted(() => ({ getUsersMock: vi.fn() }))

vi.mock('@/services/adminApi', () => ({
  adminApi: { getUsers: getUsersMock },
}))

describe('useAdminUsersQuery', () => {
  beforeEach(() => {
    getUsersMock.mockReset()
    useUserStore.setState({ adminToken: null })
  })

  it('adminToken이 없으면 쿼리가 비활성화되어 API를 호출하지 않는다', () => {
    const { result } = renderHook(() => useAdminUsersQuery(1), { wrapper: withQueryClient() })

    expect(result.current.fetchStatus).toBe('idle')
    expect(getUsersMock).not.toHaveBeenCalled()
  })

  it('adminToken이 있으면 해당 페이지의 유저 목록을 가져온다', async () => {
    useUserStore.setState({ adminToken: 'secret' })
    const response = { users: [], meta: { total: 0, page: 2, per_page: 20 } }
    getUsersMock.mockResolvedValue(response)

    const { result } = renderHook(() => useAdminUsersQuery(2), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(getUsersMock).toHaveBeenCalledWith(2)
    expect(result.current.data).toEqual(response)
  })
})
