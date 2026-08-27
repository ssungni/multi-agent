import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useUpdateInterestsMutation } from './useUpdateInterestsMutation'
import { useUserStore } from '@/stores/userStore'
import { createTestQueryClient, withQueryClient } from '@/test/test-utils'

const { updateInterestsMock } = vi.hoisted(() => ({ updateInterestsMock: vi.fn() }))

vi.mock('@/services/interestsApi', () => ({
  interestsApi: { updateInterests: updateInterestsMock },
}))

describe('useUpdateInterestsMutation', () => {
  beforeEach(() => {
    updateInterestsMock.mockReset()
    useUserStore.setState({ userId: 1, adminToken: null })
  })

  it('성공 시 interests 쿼리 캐시를 갱신한다', async () => {
    updateInterestsMock.mockResolvedValue({ interests: ['tutor_music'] })
    const queryClient = createTestQueryClient()
    const setDataSpy = vi.spyOn(queryClient, 'setQueryData')

    const { result } = renderHook(() => useUpdateInterestsMutation(), {
      wrapper: withQueryClient(queryClient),
    })

    await act(async () => {
      await result.current.mutateAsync(['tutor_music'])
    })

    expect(setDataSpy).toHaveBeenCalledWith(['interests', 1], ['tutor_music'])
  })

  it('실패 시 isError가 true가 된다', async () => {
    updateInterestsMock.mockRejectedValue(new Error('invalid_params'))

    const { result } = renderHook(() => useUpdateInterestsMutation(), {
      wrapper: withQueryClient(),
    })

    act(() => {
      result.current.mutate(['tutor_music'])
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
