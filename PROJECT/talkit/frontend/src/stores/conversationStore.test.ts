import { describe, it, expect, beforeEach } from 'vitest'
import { useConversationStore } from './conversationStore'
import type { Message } from '@/types/conversation'

describe('useConversationStore', () => {
  beforeEach(() => {
    useConversationStore.getState().reset()
  })

  it('초기 상태는 idle이며 messages/streamingContent가 비어있다', () => {
    const state = useConversationStore.getState()
    expect(state.status).toBe('idle')
    expect(state.messages).toEqual([])
    expect(state.streamingContent).toBe('')
    expect(state.error).toBeNull()
  })

  it('setStatus는 status를 변경한다', () => {
    useConversationStore.getState().setStatus('recording')
    expect(useConversationStore.getState().status).toBe('recording')
  })

  it('초기 topicId는 general_english이다', () => {
    expect(useConversationStore.getState().topicId).toBe('general_english')
  })

  it('setTopicId는 topicId를 변경한다', () => {
    useConversationStore.getState().setTopicId('workplace_english')
    expect(useConversationStore.getState().topicId).toBe('workplace_english')
  })

  it('addMessage는 messages 배열에 메시지를 추가한다', () => {
    const message: Message = { id: '1', role: 'user', content: 'hello' }
    useConversationStore.getState().addMessage(message)

    expect(useConversationStore.getState().messages).toEqual([message])
  })

  it('addMessage를 여러 번 호출하면 순서대로 누적된다', () => {
    useConversationStore.getState().addMessage({ id: '1', role: 'user', content: 'a' })
    useConversationStore.getState().addMessage({ id: '2', role: 'assistant', content: 'b' })

    const { messages } = useConversationStore.getState()
    expect(messages.map((m) => m.id)).toEqual(['1', '2'])
  })

  it('appendStreamDelta는 streamingContent에 텍스트를 누적한다', () => {
    useConversationStore.getState().appendStreamDelta('Hel')
    useConversationStore.getState().appendStreamDelta('lo')

    expect(useConversationStore.getState().streamingContent).toBe('Hello')
  })

  it('commitStreamMessage는 streamingContent를 새 assistant 메시지로 이동시키고 비운다', () => {
    useConversationStore.getState().appendStreamDelta('Hi there')
    useConversationStore.getState().commitStreamMessage('ai-1')

    const state = useConversationStore.getState()
    expect(state.streamingContent).toBe('')
    expect(state.messages).toEqual([
      { id: 'ai-1', role: 'assistant', content: 'Hi there', isStreaming: false },
    ])
  })

  it('commitStreamMessage는 기존 messages 뒤에 추가한다', () => {
    useConversationStore.getState().addMessage({ id: 'u-1', role: 'user', content: 'hi' })
    useConversationStore.getState().appendStreamDelta('hello')
    useConversationStore.getState().commitStreamMessage('ai-1')

    const ids = useConversationStore.getState().messages.map((m) => m.id)
    expect(ids).toEqual(['u-1', 'ai-1'])
  })

  it('clearStreaming은 streamingContent만 비우고 messages는 유지한다', () => {
    useConversationStore.getState().addMessage({ id: '1', role: 'user', content: 'a' })
    useConversationStore.getState().appendStreamDelta('partial')

    useConversationStore.getState().clearStreaming()

    const state = useConversationStore.getState()
    expect(state.streamingContent).toBe('')
    expect(state.messages).toHaveLength(1)
  })

  it('setError는 error를 설정하고 status를 error로 전환한다', () => {
    useConversationStore.getState().setError('네트워크 오류')

    const state = useConversationStore.getState()
    expect(state.status).toBe('error')
    expect(state.error).toBe('네트워크 오류')
  })

  it('addAudioUrl은 해당 id의 메시지에만 audioUrls를 채운다', () => {
    useConversationStore.getState().addMessage({ id: '1', role: 'assistant', content: 'a' })
    useConversationStore.getState().addMessage({ id: '2', role: 'assistant', content: 'b' })

    useConversationStore.getState().addAudioUrl('1', 'blob:audio-1')

    const [first, second] = useConversationStore.getState().messages
    expect(first!.audioUrls).toEqual(['blob:audio-1'])
    expect(second!.audioUrls).toBeUndefined()
  })

  it('addAudioUrl을 여러 번 호출하면 같은 메시지에 순서대로 누적된다 (문장별 클립)', () => {
    useConversationStore.getState().addMessage({ id: '1', role: 'assistant', content: 'a b' })

    useConversationStore.getState().addAudioUrl('1', 'blob:audio-1')
    useConversationStore.getState().addAudioUrl('1', 'blob:audio-2')

    const [first] = useConversationStore.getState().messages
    expect(first!.audioUrls).toEqual(['blob:audio-1', 'blob:audio-2'])
  })

  it('reset은 모든 상태를 초기값으로 되돌린다', () => {
    useConversationStore.getState().setStatus('tts_playing')
    useConversationStore.getState().addMessage({ id: '1', role: 'user', content: 'a' })
    useConversationStore.getState().setError('오류')
    useConversationStore.getState().setTopicId('workplace_english')

    useConversationStore.getState().reset()

    const state = useConversationStore.getState()
    expect(state.status).toBe('idle')
    expect(state.messages).toEqual([])
    expect(state.error).toBeNull()
    expect(state.streamingContent).toBe('')
    expect(state.topicId).toBe('general_english')
  })

  it('초기 mode는 practice이다', () => {
    expect(useConversationStore.getState().mode).toBe('practice')
  })

  it('setMode는 mode를 변경한다', () => {
    useConversationStore.getState().setMode('live')
    expect(useConversationStore.getState().mode).toBe('live')
  })

  it('reset()은 mode를 건드리지 않는다 (대화 세션과 별개의 선택이므로)', () => {
    useConversationStore.getState().setMode('live')
    useConversationStore.getState().reset()

    expect(useConversationStore.getState().mode).toBe('live')
  })

  it('초기 sessionStartedAt은 null이다', () => {
    expect(useConversationStore.getState().sessionStartedAt).toBeNull()
  })

  it('markSessionStarted는 sessionStartedAt을 현재 시각으로 설정한다', () => {
    const before = Date.now()
    useConversationStore.getState().markSessionStarted()
    const after = Date.now()

    const value = useConversationStore.getState().sessionStartedAt
    expect(value).not.toBeNull()
    expect(value!).toBeGreaterThanOrEqual(before)
    expect(value!).toBeLessThanOrEqual(after)
  })

  it('reset()은 sessionStartedAt을 null로 되돌린다', () => {
    useConversationStore.getState().markSessionStarted()
    useConversationStore.getState().reset()

    expect(useConversationStore.getState().sessionStartedAt).toBeNull()
  })
})
