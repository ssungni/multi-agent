import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UserTable } from './UserTable'
import type { AdminUser } from '@/types/admin'

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
  active_membership: { id: 10, plan_name: 'Premium', expires_at: '2026-08-01T12:00:00Z' },
  expired_membership: null,
}

const userWithExpiredMembership: AdminUser = {
  id: 3,
  email: 'expired@example.com',
  name: '만료유저',
  active_membership: null,
  expired_membership: { id: 11, plan_name: 'Premium', expires_at: '2026-06-19T00:00:00Z' },
}

describe('UserTable', () => {
  it('로딩 중에는 스켈레톤을 표시한다', () => {
    const { container } = render(
      <UserTable users={undefined} isLoading onGrant={vi.fn()} onRevoke={vi.fn()} />
    )
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('유저가 없으면 안내 문구를 표시한다', () => {
    render(<UserTable users={[]} isLoading={false} onGrant={vi.fn()} onRevoke={vi.fn()} />)
    expect(screen.getByText('등록된 유저가 없습니다.')).toBeInTheDocument()
  })

  it('유저 이름/이메일/id를 표시한다', () => {
    render(
      <UserTable
        users={[userWithoutMembership]}
        isLoading={false}
        onGrant={vi.fn()}
        onRevoke={vi.fn()}
      />
    )
    expect(screen.getByText('무료유저')).toBeInTheDocument()
    expect(screen.getByText('free@example.com')).toBeInTheDocument()
    expect(screen.getByText('#1')).toBeInTheDocument()
  })

  it('멤버십이 없으면 "활성 멤버십 없음" 배지와 "부여" 버튼을 표시한다', () => {
    render(
      <UserTable
        users={[userWithoutMembership]}
        isLoading={false}
        onGrant={vi.fn()}
        onRevoke={vi.fn()}
      />
    )
    expect(screen.getByText('활성 멤버십 없음')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '부여' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '삭제' })).not.toBeInTheDocument()
  })

  it('만료된 멤버십이 있으면 "활성 멤버십 없음" 대신 "만료됨" 배지를 표시한다', () => {
    render(
      <UserTable
        users={[userWithExpiredMembership]}
        isLoading={false}
        onGrant={vi.fn()}
        onRevoke={vi.fn()}
      />
    )
    expect(screen.queryByText('활성 멤버십 없음')).not.toBeInTheDocument()
    expect(screen.getByText(/Premium.*만료됨/)).toBeInTheDocument()
  })

  it('만료된 멤버십만 있어도 "부여" 버튼이 표시된다 (재구매 가능)', () => {
    render(
      <UserTable
        users={[userWithExpiredMembership]}
        isLoading={false}
        onGrant={vi.fn()}
        onRevoke={vi.fn()}
      />
    )
    expect(screen.getByRole('button', { name: '부여' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '삭제' })).not.toBeInTheDocument()
  })

  it('멤버십이 있으면 플랜/만료일 배지와 "교체"/"삭제" 버튼을 표시한다', () => {
    render(
      <UserTable
        users={[userWithMembership]}
        isLoading={false}
        onGrant={vi.fn()}
        onRevoke={vi.fn()}
      />
    )
    expect(screen.getByText(/Premium/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '교체' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '삭제' })).toBeInTheDocument()
  })

  it('부여/교체 버튼 클릭 시 onGrant가 해당 유저와 함께 호출된다', async () => {
    const onGrant = vi.fn()
    render(
      <UserTable
        users={[userWithoutMembership]}
        isLoading={false}
        onGrant={onGrant}
        onRevoke={vi.fn()}
      />
    )

    await userEvent.click(screen.getByRole('button', { name: '부여' }))

    expect(onGrant).toHaveBeenCalledWith(userWithoutMembership)
  })

  it('삭제 버튼 클릭 시 onRevoke가 membership id와 함께 호출된다', async () => {
    const onRevoke = vi.fn()
    render(
      <UserTable
        users={[userWithMembership]}
        isLoading={false}
        onGrant={vi.fn()}
        onRevoke={onRevoke}
      />
    )

    await userEvent.click(screen.getByRole('button', { name: '삭제' }))

    expect(onRevoke).toHaveBeenCalledWith(10)
  })

  it('revokingId가 해당 멤버십 id와 같으면 삭제 버튼이 비활성화되고 문구가 바뀐다', () => {
    render(
      <UserTable
        users={[userWithMembership]}
        isLoading={false}
        onGrant={vi.fn()}
        onRevoke={vi.fn()}
        revokingId={10}
      />
    )

    const button = screen.getByRole('button', { name: '삭제 중...' })
    expect(button).toBeDisabled()
  })
})
