import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PlanCard } from './PlanCard'
import type { MembershipPlan } from '@/types/membership'

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
  features: ['learning', 'conversation', 'analysis'],
  duration_days: 60,
  price_cents: 219_000,
  currency: 'KRW',
}

describe('PlanCard', () => {
  it('플랜 이름과 가격, 기간을 표시한다', () => {
    render(<PlanCard plan={basicPlan} onSelect={vi.fn()} />)

    expect(screen.getByText('베이직')).toBeInTheDocument()
    expect(screen.getByText('₩129,000')).toBeInTheDocument()
    expect(screen.getByText('/ 30일')).toBeInTheDocument()
  })

  it('conversation 기능이 포함된 플랜은 "추천" 배지를 표시한다', () => {
    render(<PlanCard plan={premiumPlan} onSelect={vi.fn()} />)
    expect(screen.getByText('추천')).toBeInTheDocument()
  })

  it('conversation이 없는 플랜은 "추천" 배지를 표시하지 않는다', () => {
    render(<PlanCard plan={basicPlan} onSelect={vi.fn()} />)
    expect(screen.queryByText('추천')).not.toBeInTheDocument()
  })

  it('포함된 기능은 일반 텍스트, 미포함 기능은 취소선으로 표시한다 (베이직 = 학습만 포함)', () => {
    render(<PlanCard plan={basicPlan} onSelect={vi.fn()} />)

    expect(screen.getByText('AI 표현 학습')).not.toHaveClass('line-through')
    expect(screen.getByText('AI 롤플레잉')).toHaveClass('line-through')
    expect(screen.getByText('AI 디스커션')).toHaveClass('line-through')
    expect(screen.getByText('무제한 AI 분석')).toHaveClass('line-through')
  })

  it('conversation 기능이 있으면 "AI 롤플레잉"과 "AI 디스커션" 둘 다 포함으로 표시한다', () => {
    render(<PlanCard plan={premiumPlan} onSelect={vi.fn()} />)

    expect(screen.getByText('AI 롤플레잉')).not.toHaveClass('line-through')
    expect(screen.getByText('AI 디스커션')).not.toHaveClass('line-through')
  })

  it('구매 버튼 클릭 시 onSelect가 plan과 함께 호출된다', async () => {
    const onSelect = vi.fn()
    render(<PlanCard plan={premiumPlan} onSelect={onSelect} />)

    await userEvent.click(screen.getByRole('button', { name: '구매' }))

    expect(onSelect).toHaveBeenCalledWith(premiumPlan)
  })

  it('isCurrentPlan이 true이면 버튼이 "현재 플랜"으로 바뀌고 비활성화된다', () => {
    render(<PlanCard plan={basicPlan} isCurrentPlan onSelect={vi.fn()} />)

    const button = screen.getByRole('button', { name: '현재 플랜' })
    expect(button).toBeDisabled()
  })

  it('isCurrentPlan이 true이면 클릭해도 onSelect가 호출되지 않는다', async () => {
    const onSelect = vi.fn()
    render(<PlanCard plan={basicPlan} isCurrentPlan onSelect={onSelect} />)

    await userEvent.click(screen.getByRole('button', { name: '현재 플랜' }))

    expect(onSelect).not.toHaveBeenCalled()
  })
})
