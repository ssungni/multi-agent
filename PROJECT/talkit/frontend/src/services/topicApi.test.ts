import { describe, it, expect, vi } from 'vitest'
import { topicApi } from './topicApi'

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }))

vi.mock('@/services/apiClient', () => ({
  apiRequest: apiRequestMock,
}))

describe('topicApi', () => {
  it('getTopics는 GET /topics를 호출한다', async () => {
    apiRequestMock.mockResolvedValue({ topics: [] })

    await topicApi.getTopics()

    expect(apiRequestMock).toHaveBeenCalledWith('/topics')
  })
})
