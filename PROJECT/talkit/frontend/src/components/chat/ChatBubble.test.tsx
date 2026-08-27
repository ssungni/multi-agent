import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChatBubble } from './ChatBubble'
import type { Message } from '@/types/conversation'

describe('ChatBubble', () => {
  it('user 메시지는 오른쪽으로 정렬된다', () => {
    const message: Message = { id: '1', role: 'user', content: '안녕하세요' }
    render(<ChatBubble message={message} />)

    expect(screen.getByText('안녕하세요')).toBeInTheDocument()
    expect(screen.getByText('안녕하세요').closest('div.flex')).toHaveClass('justify-end')
  })

  it('assistant 메시지는 왼쪽으로 정렬된다', () => {
    const message: Message = { id: '2', role: 'assistant', content: 'Hi there' }
    render(<ChatBubble message={message} />)

    expect(screen.getByText('Hi there').closest('div.flex')).toHaveClass('justify-start')
  })

  it('isStreaming이 true이면 커서 표시 span이 렌더링된다', () => {
    const message: Message = { id: '3', role: 'assistant', content: '입력 중', isStreaming: true }
    const { container } = render(<ChatBubble message={message} />)

    expect(container.querySelector('.animate-pulse')).not.toBeNull()
  })

  it('isStreaming이 없으면 커서가 렌더링되지 않는다', () => {
    const message: Message = { id: '4', role: 'assistant', content: '완료됨' }
    const { container } = render(<ChatBubble message={message} />)

    expect(container.querySelector('.animate-pulse')).toBeNull()
  })

  it('assistant + audioUrls가 있으면 재생 버튼을 표시한다', () => {
    const message: Message = {
      id: '5',
      role: 'assistant',
      content: '들어보세요',
      audioUrls: ['blob:audio-1'],
    }
    render(<ChatBubble message={message} />)

    expect(screen.getByRole('button', { name: '다시 듣기' })).toBeInTheDocument()
  })

  it('user 메시지도 audioUrls가 있으면 재생 버튼을 표시한다 (자신이 한 말 다시 듣기)', () => {
    const message: Message = {
      id: '6',
      role: 'user',
      content: '내 음성',
      audioUrls: ['blob:audio-2'],
    }
    render(<ChatBubble message={message} />)

    expect(screen.getByRole('button', { name: '다시 듣기' })).toBeInTheDocument()
  })

  it('audioUrls가 없으면 재생 버튼을 표시하지 않는다', () => {
    const message: Message = { id: '7', role: 'assistant', content: '오디오 없음' }
    render(<ChatBubble message={message} />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('audioUrls가 빈 배열이면 재생 버튼을 표시하지 않는다', () => {
    const message: Message = { id: '8', role: 'assistant', content: '오디오 없음', audioUrls: [] }
    render(<ChatBubble message={message} />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
