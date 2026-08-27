import { describe, it, expect, vi } from 'vitest'
import { roleplayApi } from './roleplayApi'

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }))

vi.mock('@/services/apiClient', () => ({
  apiRequest: apiRequestMock,
}))

describe('roleplayApi', () => {
  it('getScenarios는 GET /roleplay_scenarios를 호출한다', async () => {
    apiRequestMock.mockResolvedValue({ roleplay_scenarios: [] })

    await roleplayApi.getScenarios()

    expect(apiRequestMock).toHaveBeenCalledWith('/roleplay_scenarios')
  })
})
