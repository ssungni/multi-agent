import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlanList } from './PlanList'
import type { MembershipPlan, UserMembership } from '@/types/membership'

const basicPlan: MembershipPlan = {
  id: 1,
  name: '베이직',
  features: ['learning'],
  duration_days: 30,
  price_cents: 129_000,
  currency: 'KRW',
}

const premiumPlan: MembershipPlan = {
  id: 2,
  name: '프리미엄',
  features: ['learning', 'conversation'],
  duration_days: 60,
  price_cents: 219_000,
  currency: 'KRW',
}

describe('PlanList', () => {
  it('로딩 중에는 스켈레톤을 표시한다', () => {
    const { container } = render(
      <PlanList plans={undefined} isLoading currentMembership={null} onSelectPlan={vi.fn()} />
    )
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('플랜이 없으면 안내 문구를 표시한다', () => {
    render(<PlanList plans={[]} isLoading={false} currentMembership={null} onSelectPlan={vi.fn()} />)
    expect(screen.getByText('현재 이용 가능한 플랜이 없습니다.')).toBeInTheDocument()
  })

  it('plans가 undefined이고 로딩도 아니면 안내 문구를 표시한다', () => {
    render(
      <PlanList plans={undefined} isLoading={false} currentMembership={null} onSelectPlan={vi.fn()} />
    )
    expect(screen.getByText('현재 이용 가능한 플랜이 없습니다.')).toBeInTheDocument()
  })

  it('플랜 목록을 모두 렌더링한다', () => {
    render(
      <PlanList
        plans={[basicPlan, premiumPlan]}
        isLoading={false}
        currentMembership={null}
        onSelectPlan={vi.fn()}
      />
    )
    expect(screen.getByText('베이직')).toBeInTheDocument()
    expect(screen.getByText('프리미엄')).toBeInTheDocument()
  })

  it('가격이 비싼 플랜(프리미엄)을 왼쪽(먼저)에 렌더링한다', () => {
    // basicPlan을 먼저 넘겨도 정렬되어 프리미엄이 먼저 나와야 한다.
    render(
      <PlanList
        plans={[basicPlan, premiumPlan]}
        isLoading={false}
        currentMembership={null}
        onSelectPlan={vi.fn()}
      />
    )

    const names = screen.getAllByRole('heading', { level: 3 }).map((el) => el.textContent)
    expect(names).toEqual(['프리미엄', '베이직'])
  })

  it('currentMembership과 같은 플랜만 "현재 플랜"으로 비활성화된다', () => {
    const currentMembership: UserMembership = {
      id: 1,
      plan: { id: 1, name: '베이직', features: ['learning'] },
      starts_at: '2026-06-01T00:00:00Z',
      expires_at: '2026-07-01T00:00:00Z',
      days_remaining: 10,
    }
    render(
      <PlanList
        plans={[basicPlan, premiumPlan]}
        isLoading={false}
        currentMembership={currentMembership}
        onSelectPlan={vi.fn()}
      />
    )

    expect(screen.getByRole('button', { name: '현재 플랜' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '구매' })).toBeInTheDocument()
  })
})
