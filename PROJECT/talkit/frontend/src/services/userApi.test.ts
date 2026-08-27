import { describe, it, expect, vi } from 'vitest'
import { userApi } from './userApi'
import type { SignupRequest, LoginRequest } from '@/types/user'

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }))

vi.mock('@/services/apiClient', () => ({
  apiRequest: apiRequestMock,
}))

describe('userApi', () => {
  it('signup은 POST /users에 body를 JSON으로 직렬화해 전달한다', async () => {
    apiRequestMock.mockResolvedValue({
      user: { id: 1, email: 'a@b.com', name: '홍길동', phone_number: '010-1234-5678' },
    })
    const body: SignupRequest = {
      email: 'a@b.com',
      name: '홍길동',
      phone_number: '010-1234-5678',
      password: 'password123',
    }

    await userApi.signup(body)

    expect(apiRequestMock).toHaveBeenCalledWith('/users', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  })

  it('login은 POST /sessions에 email body를 JSON으로 직렬화해 전달한다', async () => {
    apiRequestMock.mockResolvedValue({
      user: { id: 1, email: 'a@b.com', name: '홍길동', phone_number: '010-1234-5678' },
    })
    const body: LoginRequest = { email: 'a@b.com', password: 'password123' }

    await userApi.login(body)

    expect(apiRequestMock).toHaveBeenCalledWith('/sessions', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  })
})
