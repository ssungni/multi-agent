import { describe, it, expect, vi } from 'vitest'
import { adminApi } from './adminApi'
import type { GrantMembershipRequest } from '@/types/admin'

const { apiRequestMock } = vi.hoisted(() => ({ apiRequestMock: vi.fn() }))

vi.mock('@/services/apiClient', () => ({
  apiRequest: apiRequestMock,
}))

describe('adminApi', () => {
  it('getUsers는 GET /admin/users?page= 를 admin 인증으로 호출한다', async () => {
    apiRequestMock.mockResolvedValue({ users: [], meta: { total: 0, page: 1, per_page: 20 } })

    await adminApi.getUsers(2)

    expect(apiRequestMock).toHaveBeenCalledWith('/admin/users?page=2', {}, { admin: true })
  })

  it('getUsers는 page를 생략하면 1페이지를 조회한다', async () => {
    apiRequestMock.mockResolvedValue({ users: [], meta: { total: 0, page: 1, per_page: 20 } })

    await adminApi.getUsers()

    expect(apiRequestMock).toHaveBeenCalledWith('/admin/users?page=1', {}, { admin: true })
  })

  it('getUsers에 토큰을 명시적으로 전달하면 그 토큰으로 호출한다 (토큰 검증용)', async () => {
    apiRequestMock.mockResolvedValue({ users: [], meta: { total: 0, page: 1, per_page: 20 } })

    await adminApi.getUsers(1, 'candidate-token')

    expect(apiRequestMock).toHaveBeenCalledWith(
      '/admin/users?page=1',
      {},
      { admin: true, adminToken: 'candidate-token' }
    )
  })

  it('grantMembership은 POST /admin/memberships를 admin 인증으로 호출한다', async () => {
    apiRequestMock.mockResolvedValue({ membership: {} })
    const body: GrantMembershipRequest = { user_id: 1, membership_plan_id: 2 }

    await adminApi.grantMembership(body)

    expect(apiRequestMock).toHaveBeenCalledWith(
      '/admin/memberships',
      { method: 'POST', body: JSON.stringify(body) },
      { admin: true }
    )
  })

  it('revokeMembership은 DELETE /admin/memberships/:id를 admin 인증으로 호출한다', async () => {
    apiRequestMock.mockResolvedValue({ message: '삭제됨' })

    await adminApi.revokeMembership(5)

    expect(apiRequestMock).toHaveBeenCalledWith(
      '/admin/memberships/5',
      { method: 'DELETE' },
      { admin: true }
    )
  })
})
