import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useGrantMembershipMutation } from './useGrantMembershipMutation'
import { createTestQueryClient, withQueryClient } from '@/test/test-utils'
import type { GrantMembershipRequest } from '@/types/admin'

const { grantMembershipMock } = vi.hoisted(() => ({ grantMembershipMock: vi.fn() }))

vi.mock('@/services/adminApi', () => ({
  adminApi: { grantMembership: grantMembershipMock },
}))

const body: GrantMembershipRequest = { user_id: 1, membership_plan_id: 2 }

describe('useGrantMembershipMutation', () => {
  beforeEach(() => {
    grantMembershipMock.mockReset()
  })

  it('부여 성공 시 admin users 쿼리 캐시를 무효화한다', async () => {
    grantMembershipMock.mockResolvedValue({ membership: { id: 1 } })
    const queryClient = createTestQueryClient()
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => useGrantMembershipMutation(), {
      wrapper: withQueryClient(queryClient),
    })

    await act(async () => {
      await result.current.mutateAsync(body)
    })

    expect(grantMembershipMock.mock.calls[0]?.[0]).toEqual(body)
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['admin', 'users'] })
  })
})
