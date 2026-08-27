import { describe, it, expect, vi } from 'vitest'
import { interestsApi } from './interestsApi'

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }))

vi.mock('@/services/apiClient', () => ({
  apiRequest: apiRequestMock,
}))

describe('interestsApi', () => {
  it('getInterests는 GET /me/interests를 호출한다', async () => {
    apiRequestMock.mockResolvedValue({ interests: [] })

    await interestsApi.getInterests()

    expect(apiRequestMock).toHaveBeenCalledWith('/me/interests')
  })

  it('updateInterests는 PUT /me/interests에 interests를 JSON으로 전달한다', async () => {
    apiRequestMock.mockResolvedValue({ interests: ['tutor_food'] })

    await interestsApi.updateInterests(['tutor_food', 'tutor_travel'])

    expect(apiRequestMock).toHaveBeenCalledWith('/me/interests', {
      method: 'PUT',
      body: JSON.stringify({ interests: ['tutor_food', 'tutor_travel'] }),
    })
  })
})
