import { describe, it, expect, vi } from 'vitest'
import { profileApi } from './profileApi'

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }))

vi.mock('@/services/apiClient', () => ({
  apiRequest: apiRequestMock,
}))

describe('profileApi', () => {
  it('getProfile은 GET /me/profile을 호출한다', async () => {
    apiRequestMock.mockResolvedValue({
      id: 1,
      email: 'a@b.com',
      name: '홍길동',
      phone_number: '010-1234-5678',
    })

    await profileApi.getProfile()

    expect(apiRequestMock).toHaveBeenCalledWith('/me/profile')
  })
})
