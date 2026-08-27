import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useVerifyAdminTokenMutation } from './useVerifyAdminTokenMutation'
import { withQueryClient } from '@/test/test-utils'
import { ApiError } from '@/services/apiClient'

const { getUsersMock } = vi.hoisted(() => ({ getUsersMock: vi.fn() }))

vi.mock('@/services/adminApi', () => ({
  adminApi: { getUsers: getUsersMock },
}))

describe('useVerifyAdminTokenMutation', () => {
  beforeEach(() => {
    getUsersMock.mockReset()
  })

  it('토큰이 유효하면 adminApi.getUsers(1, token)을 호출하고 성공한다', async () => {
    getUsersMock.mockResolvedValue({ users: [], meta: { total: 0, page: 1, per_page: 20 } })

    const { result } = renderHook(() => useVerifyAdminTokenMutation(), {
      wrapper: withQueryClient(),
    })

    await act(async () => {
      await result.current.mutateAsync('valid-token')
    })

    expect(getUsersMock).toHaveBeenCalledWith(1, 'valid-token')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
  })

  it('토큰이 잘못되면(401) isError가 true가 된다', async () => {
    getUsersMock.mockRejectedValue(new ApiError(401, { error: 'unauthorized' }))

    const { result } = renderHook(() => useVerifyAdminTokenMutation(), {
      wrapper: withQueryClient(),
    })

    act(() => {
      result.current.mutate('wrong-token')
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
