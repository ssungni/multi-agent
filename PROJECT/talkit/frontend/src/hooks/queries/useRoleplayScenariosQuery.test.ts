import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useRoleplayScenariosQuery } from './useRoleplayScenariosQuery'
import { withQueryClient } from '@/test/test-utils'
import type { RoleplayScenario } from '@/types/roleplay'

const { getScenariosMock } = vi.hoisted(() => ({ getScenariosMock: vi.fn() }))

vi.mock('@/services/roleplayApi', () => ({
  roleplayApi: { getScenarios: getScenariosMock },
}))

const scenarios: RoleplayScenario[] = [
  {
    id: 1,
    series_title: '직장인 필수영어',
    title: '힘 빼고 영어 잘하기',
    level: 'Basic',
    description: '설명',
    position: 1,
    topic_id: 'workplace_english',
    opening: 'opening hint',
    live_opening: 'live opening line',
  },
]

describe('useRoleplayScenariosQuery', () => {
  beforeEach(() => {
    getScenariosMock.mockReset()
  })

  it('roleplay_scenarios 배열을 반환한다', async () => {
    getScenariosMock.mockResolvedValue({ roleplay_scenarios: scenarios })

    const { result } = renderHook(() => useRoleplayScenariosQuery(), {
      wrapper: withQueryClient(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(scenarios)
  })

  it('API 에러는 그대로 전파된다', async () => {
    getScenariosMock.mockRejectedValue(new Error('network error'))

    const { result } = renderHook(() => useRoleplayScenariosQuery(), {
      wrapper: withQueryClient(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
