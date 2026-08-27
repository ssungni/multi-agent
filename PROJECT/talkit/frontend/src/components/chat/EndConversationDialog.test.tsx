import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EndConversationDialog } from './EndConversationDialog'
import type { Message } from '@/types/conversation'

const { analyzeMock } = vi.hoisted(() => ({ analyzeMock: vi.fn() }))

vi.mock('@/services/conversationApi', () => ({
  conversationApi: { analyze: analyzeMock },
}))

const messages: Message[] = [
  { id: '1', role: 'assistant', content: 'Hi there!' },
  { id: '2', role: 'user', content: 'Hello, my name is Danny.' },
]

describe('EndConversationDialog', () => {
  beforeEach(() => {
    analyzeMock.mockReset()
  })

  it('open이 false이면 내용이 보이지 않는다', () => {
    render(
      <EndConversationDialog
        open={false}
        onConfirm={vi.fn()}
        wordCount={5}
        durationLabel="1분 30초"
        messages={messages}
      />
    )
    expect(screen.queryByText('대화를 완료했어요.')).not.toBeInTheDocument()
  })

  it('open이 true이면 완료 메시지와 통계를 표시한다', () => {
    render(
      <EndConversationDialog
        open
        onConfirm={vi.fn()}
        wordCount={5}
        durationLabel="1분 30초"
        messages={messages}
      />
    )
    expect(screen.getByText('대화를 완료했어요.')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('1분 30초')).toBeInTheDocument()
  })

  it('단어 수가 적으면 "조금만 더 말해주세요" 팁을 보여준다', () => {
    render(
      <EndConversationDialog
        open
        onConfirm={vi.fn()}
        wordCount={3}
        durationLabel="n/a"
        messages={messages}
      />
    )
    expect(screen.getByText('다음엔 조금만 더 말해주세요.')).toBeInTheDocument()
  })

  it('단어 수가 충분하면 칭찬 팁을 보여준다', () => {
    render(
      <EndConversationDialog
        open
        onConfirm={vi.fn()}
        wordCount={50}
        durationLabel="2분"
        messages={messages}
      />
    )
    expect(screen.getByText('오늘 대화 정말 잘하셨어요!')).toBeInTheDocument()
  })

  it('확인 버튼을 누르면 onConfirm이 호출된다', async () => {
    const onConfirm = vi.fn()
    render(
      <EndConversationDialog
        open
        onConfirm={onConfirm}
        wordCount={5}
        durationLabel="1분"
        messages={messages}
      />
    )
    await userEvent.click(screen.getByRole('button', { name: '확인' }))
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('AI 분석 요청을 누르면 messages를 role/content로만 전달해 분석을 요청하고 결과를 표시한다', async () => {
    analyzeMock.mockResolvedValue({ analysis: '잘하셨어요! 핵심 표현: "My name is ~"' })

    render(
      <EndConversationDialog
        open
        onConfirm={vi.fn()}
        wordCount={5}
        durationLabel="1분"
        messages={messages}
      />
    )

    await userEvent.click(screen.getByRole('button', { name: 'AI 분석 요청' }))

    expect(analyzeMock).toHaveBeenCalledWith([
      { role: 'assistant', content: 'Hi there!' },
      { role: 'user', content: 'Hello, my name is Danny.' },
    ])

    await waitFor(() =>
      expect(screen.getByText('잘하셨어요! 핵심 표현: "My name is ~"')).toBeInTheDocument()
    )
    expect(screen.getByText('AI 분석 결과')).toBeInTheDocument()
  })

  it('분석 요청이 실패하면 에러 메시지를 보여준다', async () => {
    analyzeMock.mockRejectedValue(new Error('network error'))

    render(
      <EndConversationDialog
        open
        onConfirm={vi.fn()}
        wordCount={5}
        durationLabel="1분"
        messages={messages}
      />
    )

    await userEvent.click(screen.getByRole('button', { name: 'AI 분석 요청' }))

    await waitFor(() =>
      expect(screen.getByText('분석에 실패했습니다. 다시 시도해주세요.')).toBeInTheDocument()
    )
  })

  it('분석 결과를 받으면 AI 분석 요청 버튼이 비활성화된다 (중복 요청 방지)', async () => {
    analyzeMock.mockResolvedValue({ analysis: '좋아요!' })

    render(
      <EndConversationDialog
        open
        onConfirm={vi.fn()}
        wordCount={5}
        durationLabel="1분"
        messages={messages}
      />
    )

    const analyzeButton = screen.getByRole('button', { name: 'AI 분석 요청' })
    await userEvent.click(analyzeButton)

    await waitFor(() => expect(screen.getByText('좋아요!')).toBeInTheDocument())
    expect(analyzeButton).toBeDisabled()
  })
})
