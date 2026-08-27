import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useRevokeMembershipMutation } from './useRevokeMembershipMutation'
import { createTestQueryClient, withQueryClient } from '@/test/test-utils'

const { revokeMembershipMock } = vi.hoisted(() => ({ revokeMembershipMock: vi.fn() }))

vi.mock('@/services/adminApi', () => ({
  adminApi: { revokeMembership: revokeMembershipMock },
}))

describe('useRevokeMembershipMutation', () => {
  beforeEach(() => {
    revokeMembershipMock.mockReset()
  })

  it('삭제 성공 시 admin users 쿼리 캐시를 무효화한다', async () => {
    revokeMembershipMock.mockResolvedValue({ message: '삭제됨' })
    const queryClient = createTestQueryClient()
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => useRevokeMembershipMutation(), {
      wrapper: withQueryClient(queryClient),
    })

    await act(async () => {
      await result.current.mutateAsync(5)
    })

    expect(revokeMembershipMock).toHaveBeenCalledWith(5)
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['admin', 'users'] })
  })
})
