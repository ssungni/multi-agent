import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithRouter } from '@/test/test-utils'
import { ActiveMembershipCard } from './ActiveMembershipCard'
import type { UserMembership } from '@/types/membership'

const premiumMembership: UserMembership = {
  id: 1,
  plan: { id: 2, name: '프리미엄', features: ['learning', 'conversation', 'analysis'] },
  starts_at: '2026-06-01T12:00:00Z',
  expires_at: '2026-08-01T12:00:00Z',
  days_remaining: 30,
}

const basicMembership: UserMembership = {
  id: 2,
  plan: { id: 1, name: '베이직', features: ['learning'] },
  starts_at: '2026-06-01T12:00:00Z',
  expires_at: '2026-07-01T12:00:00Z',
  days_remaining: 3,
}

describe('ActiveMembershipCard', () => {
  it('로딩 중에는 스켈레톤을 표시한다', () => {
    const { container } = renderWithRouter(
      <ActiveMembershipCard membership={null} isLoading />
    )
    expect(container.querySelector('.animate-pulse')).not.toBeNull()
  })

  it('멤버십이 없으면 "활성 멤버십 없음" 안내를 표시한다', () => {
    renderWithRouter(<ActiveMembershipCard membership={null} isLoading={false} />)
    expect(screen.getByText('활성 멤버십 없음')).toBeInTheDocument()
  })

  it('conversation 기능이 있으면 AI 튜터/AI 롤플레이/토픽 버튼을 이 순서로 표시한다', () => {
    renderWithRouter(<ActiveMembershipCard membership={premiumMembership} isLoading={false} />)

    const links = screen.getAllByRole('link')
    expect(links.map((l) => l.textContent)).toEqual(['AI 튜터', 'AI 롤플레이', '토픽'])
    expect(screen.getByRole('link', { name: 'AI 튜터' })).toHaveAttribute('href', '/tutor')
    expect(screen.getByRole('link', { name: 'AI 롤플레이' })).toHaveAttribute('href', '/roleplay')
    expect(screen.getByRole('link', { name: '토픽' })).toHaveAttribute('href', '/topics')
  })

  it('conversation 기능이 없으면 토픽 버튼만 표시한다 (베이직)', () => {
    renderWithRouter(<ActiveMembershipCard membership={basicMembership} isLoading={false} />)

    expect(screen.queryByRole('link', { name: 'AI 튜터' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'AI 롤플레이' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: '토픽' })).toHaveAttribute('href', '/topics')
  })

  it('남은 일수가 LOW_DAYS_THRESHOLD 이하이면 만료 임박 표시를 한다', () => {
    renderWithRouter(<ActiveMembershipCard membership={basicMembership} isLoading={false} />)
    expect(screen.getByText(/곧 만료/)).toBeInTheDocument()
  })

  it('남은 일수가 충분하면 만료 임박 표시를 하지 않는다', () => {
    renderWithRouter(<ActiveMembershipCard membership={premiumMembership} isLoading={false} />)
    expect(screen.queryByText(/곧 만료/)).not.toBeInTheDocument()
  })

  it('플랜의 기능 배지를 모두 표시한다', () => {
    renderWithRouter(<ActiveMembershipCard membership={premiumMembership} isLoading={false} />)

    expect(screen.getByText('AI 표현 학습')).toBeInTheDocument()
    expect(screen.getByText('AI 롤플레잉')).toBeInTheDocument()
    expect(screen.getByText('무제한 AI 분석')).toBeInTheDocument()
  })

  it('플랜 이름과 남은 일수를 표시한다', () => {
    renderWithRouter(<ActiveMembershipCard membership={premiumMembership} isLoading={false} />)

    expect(screen.getByText('프리미엄')).toBeInTheDocument()
    expect(screen.getByText('30일 남음')).toBeInTheDocument()
  })
})
