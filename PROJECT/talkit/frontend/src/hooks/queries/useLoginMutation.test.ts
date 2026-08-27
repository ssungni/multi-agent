import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useLoginMutation } from './useLoginMutation'
import { withQueryClient } from '@/test/test-utils'
import type { LoginRequest } from '@/types/user'

const { loginMock } = vi.hoisted(() => ({ loginMock: vi.fn() }))

vi.mock('@/services/userApi', () => ({
  userApi: { login: loginMock },
}))

const body: LoginRequest = { email: 'exists@example.com', password: 'password123' }

describe('useLoginMutation', () => {
  beforeEach(() => {
    loginMock.mockReset()
  })

  it('로그인 성공 시 user를 반환한다', async () => {
    const response = {
      user: { id: 7, email: 'exists@example.com', name: '기존유저', phone_number: '010-0000-0000' },
    }
    loginMock.mockResolvedValue(response)

    const { result } = renderHook(() => useLoginMutation(), { wrapper: withQueryClient() })

    let data: typeof response | undefined
    await act(async () => {
      data = await result.current.mutateAsync(body)
    })

    expect(loginMock.mock.calls[0]?.[0]).toEqual(body)
    expect(data).toEqual(response)
  })

  it('로그인 실패(이메일/비밀번호 불일치) 시 isError가 true가 된다', async () => {
    loginMock.mockRejectedValue(new Error('invalid_credentials'))

    const { result } = renderHook(() => useLoginMutation(), { wrapper: withQueryClient() })

    act(() => {
      result.current.mutate(body)
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
