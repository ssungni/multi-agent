import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { GrantMembershipModal } from './GrantMembershipModal'
import { ApiError } from '@/services/apiClient'
import type { AdminUser } from '@/types/admin'
import type { MembershipPlan } from '@/types/membership'

const { usePlansQueryMock, useGrantMembershipMutationMock } = vi.hoisted(() => ({
  usePlansQueryMock: vi.fn(),
  useGrantMembershipMutationMock: vi.fn(),
}))

vi.mock('@/hooks/queries/usePlansQuery', () => ({
  usePlansQuery: usePlansQueryMock,
}))
vi.mock('@/hooks/queries/useGrantMembershipMutation', () => ({
  useGrantMembershipMutation: useGrantMembershipMutationMock,
}))

const basicPlan: MembershipPlan = {
  id: 1,
  name: 'Basic',
  features: ['learning'],
  duration_days: 30,
  price_cents: 129_000,
  currency: 'KRW',
}

const premiumPlan: MembershipPlan = {
  id: 2,
  name: 'Premium',
  features: ['learning', 'conversation', 'analysis'],
  duration_days: 60,
  price_cents: 219_000,
  currency: 'KRW',
}

const userWithoutMembership: AdminUser = {
  id: 1,
  email: 'free@example.com',
  name: '무료유저',
  active_membership: null,
  expired_membership: null,
}

const userWithMembership: AdminUser = {
  id: 2,
  email: 'premium@example.com',
  name: '프리미엄유저',
  active_membership: { id: 10, plan_name: 'Basic', expires_at: '2026-08-01T12:00:00Z' },
  expired_membership: null,
}

function mockMutationState(overrides: Record<string, unknown> = {}) {
  const state = {
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null as unknown,
    reset: vi.fn(),
    ...overrides,
  }
  useGrantMembershipMutationMock.mockReturnValue(state)
  return state
}

describe('GrantMembershipModal', () => {
  beforeEach(() => {
    usePlansQueryMock.mockReset()
    useGrantMembershipMutationMock.mockReset()
    usePlansQueryMock.mockReturnValue({ data: [basicPlan, premiumPlan], isLoading: false })
  })

  it('user가 null이면 아무것도 렌더링하지 않는다', () => {
    mockMutationState()
    const { container } = render(
      <GrantMembershipModal user={null} open onOpenChange={vi.fn()} />
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('유저 이름과 플랜 목록을 표시한다', () => {
    mockMutationState()
    render(<GrantMembershipModal user={userWithoutMembership} open onOpenChange={vi.fn()} />)

    expect(screen.getByText('무료유저님에게 멤버십 부여')).toBeInTheDocument()
    expect(screen.getByText('Basic')).toBeInTheDocument()
    expect(screen.getByText('Premium')).toBeInTheDocument()
  })

  it('기존 멤버십이 있으면 교체 안내 문구를 표시한다', () => {
    mockMutationState()
    render(<GrantMembershipModal user={userWithMembership} open onOpenChange={vi.fn()} />)

    expect(screen.getByText(/기존 Basic 멤버십은 자동으로 교체/)).toBeInTheDocument()
  })

  it('플랜을 선택하지 않으면 부여하기 버튼이 비활성화된다', () => {
    mockMutationState()
    render(<GrantMembershipModal user={userWithoutMembership} open onOpenChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: '부여하기' })).toBeDisabled()
  })

  it('플랜 선택 후 부여하기 클릭 시 mutate가 올바른 파라미터로 호출된다', async () => {
    const { mutate } = mockMutationState()
    render(<GrantMembershipModal user={userWithoutMembership} open onOpenChange={vi.fn()} />)

    await userEvent.click(screen.getByText('Premium'))
    await userEvent.click(screen.getByRole('button', { name: '부여하기' }))

    expect(mutate).toHaveBeenCalledWith(
      { user_id: 1, membership_plan_id: 2 },
      expect.objectContaining({ onSuccess: expect.any(Function) })
    )
  })

  it('isPending이면 버튼에 진행 중 문구가 표시된다', async () => {
    mockMutationState({ isPending: true })
    render(<GrantMembershipModal user={userWithoutMembership} open onOpenChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: '부여 중...' })).toBeDisabled()
  })

  it('ApiError의 message가 있으면 에러 메시지를 표시한다', () => {
    mockMutationState({
      isError: true,
      error: new ApiError(404, { error: 'user_not_found', message: '유저를 찾을 수 없습니다.' }),
    })
    render(<GrantMembershipModal user={userWithoutMembership} open onOpenChange={vi.fn()} />)

    expect(screen.getByText('유저를 찾을 수 없습니다.')).toBeInTheDocument()
  })

  it('취소 버튼 클릭 시 onOpenChange(false)가 호출된다', async () => {
    mockMutationState()
    const onOpenChange = vi.fn()
    render(<GrantMembershipModal user={userWithoutMembership} open onOpenChange={onOpenChange} />)

    await userEvent.click(screen.getByRole('button', { name: '취소' }))

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})
