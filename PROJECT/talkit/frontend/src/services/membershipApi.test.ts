import { describe, it, expect, vi } from 'vitest'
import { membershipApi } from './membershipApi'

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }))

vi.mock('@/services/apiClient', () => ({
  apiRequest: apiRequestMock,
}))

describe('membershipApi', () => {
  it('getPlans는 GET /membership_plans를 호출한다', async () => {
    apiRequestMock.mockResolvedValue({ plans: [] })

    await membershipApi.getPlans()

    expect(apiRequestMock).toHaveBeenCalledWith('/membership_plans')
  })

  it('getMyMembership은 GET /me/membership을 호출한다', async () => {
    apiRequestMock.mockResolvedValue({ membership: null })

    await membershipApi.getMyMembership()

    expect(apiRequestMock).toHaveBeenCalledWith('/me/membership')
  })
})
