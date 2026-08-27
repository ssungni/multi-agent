import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { OfflineBanner } from './OfflineBanner'

describe('OfflineBanner', () => {
  afterEach(() => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true })
  })

  it('온라인 상태에서는 아무것도 렌더링하지 않는다', () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true })
    render(<OfflineBanner />)

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('오프라인 상태에서는 네트워크 연결 오류 배너를 표시한다', () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true })
    render(<OfflineBanner />)

    expect(screen.getByRole('alert')).toHaveTextContent('네트워크 연결 오류')
  })

  it("'offline' 이벤트가 발생하면 배너가 나타난다", () => {
    render(<OfflineBanner />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    act(() => {
      window.dispatchEvent(new Event('offline'))
    })

    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it("'online' 이벤트가 발생하면 배너가 사라진다", () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true })
    render(<OfflineBanner />)
    expect(screen.getByRole('alert')).toBeInTheDocument()

    act(() => {
      window.dispatchEvent(new Event('online'))
    })

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
