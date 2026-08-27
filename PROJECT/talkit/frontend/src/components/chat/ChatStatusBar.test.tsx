import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChatStatusBar } from './ChatStatusBar'
import type { ConversationStatus } from '@/types/conversation'

describe('ChatStatusBar', () => {
  it('idle 상태에서는 안내 문구를 표시하고 스피너는 없다', () => {
    const { container } = render(<ChatStatusBar status="idle" error={null} />)

    expect(screen.getByText('마이크 버튼을 눌러 대화를 시작하세요')).toBeInTheDocument()
    expect(container.querySelector('.animate-spin')).toBeNull()
  })

  const spinningStatuses: ConversationStatus[] = [
    'ai_opening',
    'vad_processing',
    'stt_processing',
    'llm_streaming',
    'tts_playing',
  ]

  it.each(spinningStatuses)('%s 상태에서는 스피너가 표시된다', (status) => {
    const { container } = render(<ChatStatusBar status={status} error={null} />)
    expect(container.querySelector('.animate-spin')).not.toBeNull()
  })

  it('recording 상태에서는 스피너 없이 안내 문구만 표시한다', () => {
    const { container } = render(<ChatStatusBar status="recording" error={null} />)

    expect(screen.getByText(/녹음 중/)).toBeInTheDocument()
    expect(container.querySelector('.animate-spin')).toBeNull()
  })

  it('error 상태에서는 error 메시지를 강조 색상으로 표시한다', () => {
    render(<ChatStatusBar status="error" error="음성 인식 실패" />)

    const label = screen.getByText('음성 인식 실패')
    expect(label).toHaveClass('text-destructive')
  })

  it('error 상태인데 error 메시지가 null이면 기본 문구를 표시한다', () => {
    render(<ChatStatusBar status="error" error={null} />)

    expect(screen.getByText('알 수 없는 오류')).toBeInTheDocument()
  })

  it('recording 상태 + isMuted일 때는 음소거 안내 문구를 표시한다', () => {
    render(<ChatStatusBar status="recording" error={null} isMuted />)

    expect(screen.getByText(/음소거 중/)).toBeInTheDocument()
    expect(screen.queryByText(/답변 완료 버튼을 눌러 전송/)).not.toBeInTheDocument()
  })

  it('recording 상태 + isMuted가 아닐 때는 기존 안내 문구를 표시한다', () => {
    render(<ChatStatusBar status="recording" error={null} isMuted={false} />)

    expect(screen.getByText(/답변 완료 버튼을 눌러 전송/)).toBeInTheDocument()
  })
})
