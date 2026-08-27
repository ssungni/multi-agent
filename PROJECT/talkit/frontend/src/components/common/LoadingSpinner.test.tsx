import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingSpinner } from './LoadingSpinner'

describe('LoadingSpinner', () => {
  it('label 없이도 스피너를 렌더링한다', () => {
    const { container } = render(<LoadingSpinner />)
    expect(container.querySelector('.animate-spin')).not.toBeNull()
  })

  it('label이 있으면 텍스트로 표시한다', () => {
    render(<LoadingSpinner label="불러오는 중..." />)
    expect(screen.getByText('불러오는 중...')).toBeInTheDocument()
  })

  it('label이 없으면 텍스트를 렌더링하지 않는다', () => {
    const { container } = render(<LoadingSpinner />)
    expect(container.querySelector('span')).toBeNull()
  })

  it.each([
    ['sm', 'h-4'],
    ['md', 'h-6'],
    ['lg', 'h-8'],
  ] as const)('size=%s이면 %s 클래스를 적용한다', (size, expectedClass) => {
    const { container } = render(<LoadingSpinner size={size} />)
    expect(container.querySelector(`.${expectedClass}`)).not.toBeNull()
  })
})
