import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MessageList } from './MessageList'
import type { Message } from '@/types/conversation'

describe('MessageList', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('메시지와 streamingContent가 모두 없으면 안내 문구를 표시한다', () => {
    render(<MessageList messages={[]} streamingContent="" />)
    expect(screen.getByText('AI 튜터가 인사말을 시작합니다...')).toBeInTheDocument()
  })

  it('messages를 순서대로 렌더링한다', () => {
    const messages: Message[] = [
      { id: '1', role: 'assistant', content: '첫 메시지' },
      { id: '2', role: 'user', content: '두번째 메시지' },
    ]
    render(<MessageList messages={messages} streamingContent="" />)

    const rendered = screen.getAllByText(/메시지/)
    expect(rendered.map((el) => el.textContent)).toEqual(['첫 메시지', '두번째 메시지'])
  })

  it('streamingContent가 있으면 스트리밍 버블을 추가로 렌더링한다', () => {
    const messages: Message[] = [{ id: '1', role: 'user', content: '질문' }]
    render(<MessageList messages={messages} streamingContent="응답 중..." />)

    expect(screen.getByText('질문')).toBeInTheDocument()
    expect(screen.getByText('응답 중...')).toBeInTheDocument()
  })

  it('메시지가 있지만 streamingContent가 비어있으면 안내 문구는 표시하지 않는다', () => {
    const messages: Message[] = [{ id: '1', role: 'user', content: '안녕' }]
    render(<MessageList messages={messages} streamingContent="" />)

    expect(screen.queryByText('AI 튜터가 인사말을 시작합니다...')).not.toBeInTheDocument()
  })

  it('messages.length 또는 streamingContent가 바뀌면 scrollIntoView를 호출한다', () => {
    const scrollSpy = vi.spyOn(Element.prototype, 'scrollIntoView')
    const { rerender } = render(<MessageList messages={[]} streamingContent="" />)

    expect(scrollSpy).toHaveBeenCalled()

    rerender(
      <MessageList
        messages={[{ id: '1', role: 'user', content: 'hi' }]}
        streamingContent=""
      />
    )

    expect(scrollSpy).toHaveBeenCalledTimes(2)
  })
})
