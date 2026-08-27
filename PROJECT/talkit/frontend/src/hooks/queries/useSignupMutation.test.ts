import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useSignupMutation } from './useSignupMutation'
import { withQueryClient } from '@/test/test-utils'
import type { SignupRequest } from '@/types/user'

const { signupMock } = vi.hoisted(() => ({ signupMock: vi.fn() }))

vi.mock('@/services/userApi', () => ({
  userApi: { signup: signupMock },
}))

const body: SignupRequest = {
  email: 'new@example.com',
  name: '신규유저',
  phone_number: '010-1234-5678',
  password: 'password123',
}

describe('useSignupMutation', () => {
  beforeEach(() => {
    signupMock.mockReset()
  })

  it('가입 성공 시 생성된 user를 반환한다', async () => {
    const response = { user: { id: 7, email: 'new@example.com', name: '신규유저' } }
    signupMock.mockResolvedValue(response)

    const { result } = renderHook(() => useSignupMutation(), { wrapper: withQueryClient() })

    let data: typeof response | undefined
    await act(async () => {
      data = await result.current.mutateAsync(body)
    })

    // mutationFn은 variables 외에 TanStack Query의 내부 컨텍스트 객체도 함께 받으므로
    // 첫 번째 인자(실제 우리가 전달한 변수)만 검증한다.
    expect(signupMock.mock.calls[0]?.[0]).toEqual(body)
    expect(data).toEqual(response)
  })

  it('가입 실패 시 isError가 true가 된다', async () => {
    signupMock.mockRejectedValue(new Error('email_taken'))

    const { result } = renderHook(() => useSignupMutation(), { wrapper: withQueryClient() })

    act(() => {
      result.current.mutate(body)
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
