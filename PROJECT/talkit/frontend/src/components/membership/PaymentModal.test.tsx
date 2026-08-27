import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PaymentModal } from './PaymentModal'
import { ApiError } from '@/services/apiClient'
import { MOCK_CARD_TOKENS } from '@/lib/constants'
import type { MembershipPlan } from '@/types/membership'

const { usePaymentMutationMock } = vi.hoisted(() => ({ usePaymentMutationMock: vi.fn() }))

vi.mock('@/hooks/queries/usePaymentMutation', () => ({
  usePaymentMutation: usePaymentMutationMock,
}))

const premiumPlan: MembershipPlan = {
  id: 2,
  name: '프리미엄',
  features: ['learning', 'conversation'],
  duration_days: 60,
  price_cents: 219_000,
  currency: 'KRW',
}

function defaultMutationState() {
  return {
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null as unknown,
    reset: vi.fn(),
  }
}

function mockMutation(overrides: Partial<ReturnType<typeof defaultMutationState>> = {}) {
  const state = { ...defaultMutationState(), ...overrides }
  usePaymentMutationMock.mockReturnValue(state)
  return state
}

describe('PaymentModal', () => {
  beforeEach(() => {
    usePaymentMutationMock.mockReset()
  })

  it('plan이 null이면 아무것도 렌더링하지 않는다', () => {
    mockMutation()
    const { container } = render(<PaymentModal plan={null} open onOpenChange={vi.fn()} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('플랜 요약 정보를 표시한다', () => {
    mockMutation()
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    expect(screen.getByText('프리미엄 결제')).toBeInTheDocument()
    expect(screen.getByText('60일')).toBeInTheDocument()
    expect(screen.getAllByText('₩219,000').length).toBeGreaterThan(0)
  })

  it('카드 토큰 입력 기본값은 성공 토큰이다', () => {
    mockMutation()
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    expect(screen.getByLabelText('카드 토큰 (Mock)')).toHaveValue(MOCK_CARD_TOKENS.success)
  })

  it('결제하기 클릭 시 바로 mutate를 호출하지 않고 확인 단계를 보여준다', async () => {
    const { mutate } = mockMutation()
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    await userEvent.click(screen.getByRole('button', { name: /결제하기/ }))

    expect(screen.getByText('결제하시겠습니까?')).toBeInTheDocument()
    expect(mutate).not.toHaveBeenCalled()
  })

  it('확인 단계에서 "네, 결제할게요" 클릭 시 mutate가 올바른 파라미터로 호출된다', async () => {
    const { mutate } = mockMutation()
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    await userEvent.click(screen.getByRole('button', { name: /결제하기/ }))
    await userEvent.click(screen.getByRole('button', { name: '네, 결제할게요' }))

    expect(mutate).toHaveBeenCalledWith(
      {
        membership_plan_id: premiumPlan.id,
        payment_method: 'card',
        card_token: MOCK_CARD_TOKENS.success,
      },
      expect.objectContaining({ onSuccess: expect.any(Function), onError: expect.any(Function) })
    )
  })

  it('확인 단계에서 취소를 누르면 mutate 없이 입력 폼으로 돌아간다', async () => {
    const { mutate } = mockMutation()
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    await userEvent.click(screen.getByRole('button', { name: /결제하기/ }))
    expect(screen.getByText('결제하시겠습니까?')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: '취소' }))

    expect(screen.getByLabelText('카드 토큰 (Mock)')).toBeInTheDocument()
    expect(mutate).not.toHaveBeenCalled()
  })

  it('카드 토큰을 비우면 결제 버튼이 비활성화된다', async () => {
    mockMutation()
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    await userEvent.clear(screen.getByLabelText('카드 토큰 (Mock)'))

    expect(screen.getByRole('button', { name: /결제하기/ })).toBeDisabled()
  })

  it('isPending이면 결제 버튼에 진행 중 문구가 표시되고 비활성화된다', () => {
    mockMutation({ isPending: true })
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: '결제 처리 중...' })).toBeDisabled()
  })

  it('ApiError의 message가 있으면 그 메시지를 표시한다', () => {
    mockMutation({
      isError: true,
      error: new ApiError(422, { error: 'payment_failed', message: '카드 잔액이 부족합니다.' }),
    })
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    expect(screen.getByText('카드 잔액이 부족합니다.')).toBeInTheDocument()
  })

  it('ApiError에 message가 없으면 에러 코드를 포함한 기본 문구를 표시한다', () => {
    mockMutation({
      isError: true,
      error: new ApiError(422, { error: 'payment_failed' }),
    })
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    expect(screen.getByText('결제 실패: payment_failed')).toBeInTheDocument()
  })

  it('ApiError가 아닌 일반 에러는 공통 안내 문구를 표시한다', () => {
    mockMutation({ isError: true, error: new Error('boom') })
    render(<PaymentModal plan={premiumPlan} open onOpenChange={vi.fn()} />)

    expect(
      screen.getByText('결제 중 오류가 발생했습니다. 다시 시도해주세요.')
    ).toBeInTheDocument()
  })

  it('취소 버튼 클릭 시 onOpenChange(false)가 호출된다', async () => {
    mockMutation()
    const onOpenChange = vi.fn()
    render(<PaymentModal plan={premiumPlan} open onOpenChange={onOpenChange} />)

    await userEvent.click(screen.getByRole('button', { name: '취소' }))

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})
