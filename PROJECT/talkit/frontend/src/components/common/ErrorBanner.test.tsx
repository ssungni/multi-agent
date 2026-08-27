import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorBanner } from './ErrorBanner'

describe('ErrorBanner', () => {
  it('기본 메시지를 표시한다', () => {
    render(<ErrorBanner />)
    expect(screen.getByText('데이터를 불러오는 중 오류가 발생했습니다.')).toBeInTheDocument()
  })

  it('커스텀 메시지를 표시한다', () => {
    render(<ErrorBanner message="플랜을 불러오지 못했습니다." />)
    expect(screen.getByText('플랜을 불러오지 못했습니다.')).toBeInTheDocument()
  })

  it('onRetry가 없으면 재시도 버튼을 표시하지 않는다', () => {
    render(<ErrorBanner />)
    expect(screen.queryByRole('button', { name: /재시도/ })).not.toBeInTheDocument()
  })

  it('onRetry가 있으면 재시도 버튼을 표시하고 클릭 시 호출한다', async () => {
    const onRetry = vi.fn()
    render(<ErrorBanner onRetry={onRetry} />)

    await userEvent.click(screen.getByRole('button', { name: /재시도/ }))

    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
