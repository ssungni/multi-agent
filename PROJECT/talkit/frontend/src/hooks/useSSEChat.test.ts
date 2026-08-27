import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSSEChat } from './useSSEChat'

const { chatStreamMock } = vi.hoisted(() => ({ chatStreamMock: vi.fn() }))

vi.mock('@/services/conversationApi', () => ({
  conversationApi: { chatStream: chatStreamMock },
}))

function makeSseResponse(lines: string[], opts: { ok?: boolean; status?: number } = {}): Response {
  const encoder = new TextEncoder()
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const line of lines) controller.enqueue(encoder.encode(line))
      controller.close()
    },
  })
  return { ok: opts.ok ?? true, status: opts.status ?? 200, body } as unknown as Response
}

function makeCallbacks() {
  return {
    onDelta: vi.fn(),
    onSentence: vi.fn(),
    onDone: vi.fn(),
    onError: vi.fn(),
  }
}

describe('useSSEChat', () => {
  beforeEach(() => {
    chatStreamMock.mockReset()
  })

  it('스트림 중 완성된 문장마다 onSentence를 호출하고, 마지막 미완성 텍스트는 onDone(remainder)로 전달한다', async () => {
    // 실제 백엔드(ChatController)가 보내는 형식: { delta: "..." } (OpenAI raw chunk 형식이 아님)
    chatStreamMock.mockResolvedValue(
      makeSseResponse([
        'data: {"delta":"Hello world. "}\n\n',
        'data: {"delta":"How are you? "}\n\n',
        'data: {"delta":"Great"}\n\n',
        'data: [DONE]\n\n',
      ])
    )

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([{ role: 'user', content: 'hi' }], 'general_english', callbacks)
    })

    expect(callbacks.onDelta).toHaveBeenCalledTimes(3)
    expect(callbacks.onSentence).toHaveBeenNthCalledWith(1, 'Hello world.')
    expect(callbacks.onSentence).toHaveBeenNthCalledWith(2, 'How are you?')
    expect(callbacks.onDone).toHaveBeenCalledWith('Great')
    expect(callbacks.onError).not.toHaveBeenCalled()
  })

  it('[DONE] 없이 스트림이 끝나면 남은 텍스트로 onDone을 호출한다', async () => {
    chatStreamMock.mockResolvedValue(makeSseResponse(['data: {"delta":"partial text"}\n\n']))

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([], 'general_english', callbacks)
    })

    expect(callbacks.onDone).toHaveBeenCalledWith('partial text')
  })

  it('회귀 방지: OpenAI raw chunk 형식({choices:[...]})은 더 이상 지원하지 않는다 — 백엔드는 {delta} 평탄 구조로 보낸다', async () => {
    chatStreamMock.mockResolvedValue(
      makeSseResponse([
        'data: {"choices":[{"delta":{"content":"this should be ignored"}}]}\n\n',
        'data: [DONE]\n\n',
      ])
    )

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([], 'general_english', callbacks)
    })

    // choices 형식은 더 이상 매칭되지 않으므로 delta가 전혀 누적되지 않아야 한다.
    expect(callbacks.onDelta).not.toHaveBeenCalled()
    expect(callbacks.onDone).toHaveBeenCalledWith('')
  })

  it('파싱 불가능한 data 라인은 조용히 무시한다', async () => {
    chatStreamMock.mockResolvedValue(
      makeSseResponse(['data: not-json\n\n', 'data: {"delta":"ok. "}\n\n', 'data: [DONE]\n\n'])
    )

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([], 'general_english', callbacks)
    })

    expect(callbacks.onSentence).toHaveBeenCalledWith('ok.')
    expect(callbacks.onError).not.toHaveBeenCalled()
  })

  it('wrapUp을 전달하면 conversationApi.chatStream에 그대로 forwarding한다', async () => {
    chatStreamMock.mockResolvedValue(makeSseResponse(['data: [DONE]\n\n']))

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([], 'general_english', callbacks, true)
    })

    expect(chatStreamMock).toHaveBeenCalledWith(
      [],
      'general_english',
      expect.any(AbortSignal),
      true,
      'practice'
    )
  })

  it('wrapUp/mode를 생략하면 각각 false/practice 기본값으로 전달한다', async () => {
    chatStreamMock.mockResolvedValue(makeSseResponse(['data: [DONE]\n\n']))

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([], 'general_english', callbacks)
    })

    expect(chatStreamMock).toHaveBeenCalledWith(
      [],
      'general_english',
      expect.any(AbortSignal),
      false,
      'practice'
    )
  })

  it('mode를 live로 전달하면 conversationApi.chatStream에 그대로 forwarding한다', async () => {
    chatStreamMock.mockResolvedValue(makeSseResponse(['data: [DONE]\n\n']))

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([], 'general_english', callbacks, false, 'live')
    })

    expect(chatStreamMock).toHaveBeenCalledWith(
      [],
      'general_english',
      expect.any(AbortSignal),
      false,
      'live'
    )
  })

  it('응답이 ok:false이면 onError를 호출한다', async () => {
    chatStreamMock.mockResolvedValue(makeSseResponse([], { ok: false, status: 500 }))

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([], 'general_english', callbacks)
    })

    expect(callbacks.onError).toHaveBeenCalledTimes(1)
    expect((callbacks.onError.mock.calls[0]![0] as Error).message).toBe('Chat failed: 500')
    expect(callbacks.onDone).not.toHaveBeenCalled()
  })

  it('fetch 자체가 reject되면 onError를 호출한다', async () => {
    chatStreamMock.mockRejectedValue(new Error('network down'))

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([], 'general_english', callbacks)
    })

    expect(callbacks.onError).toHaveBeenCalledTimes(1)
  })

  it('AbortError는 onError를 호출하지 않는다', async () => {
    const abortError = new DOMException('aborted', 'AbortError')
    chatStreamMock.mockRejectedValue(abortError)

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    await act(async () => {
      await result.current.send([], 'general_english', callbacks)
    })

    expect(callbacks.onError).not.toHaveBeenCalled()
    expect(callbacks.onDone).not.toHaveBeenCalled()
  })

  it('abort()를 호출하면 진행 중인 요청의 signal이 abort 처리된다', async () => {
    let capturedSignal: AbortSignal | undefined
    chatStreamMock.mockImplementation((_messages: unknown, _topicId: unknown, signal: AbortSignal) => {
      capturedSignal = signal
      return new Promise<Response>(() => {}) // 응답이 오지 않는 상태를 시뮬레이션
    })

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    act(() => {
      void result.current.send([], 'general_english', callbacks)
    })

    await vi.waitFor(() => expect(capturedSignal).toBeDefined())

    act(() => {
      result.current.abort()
    })

    expect(capturedSignal!.aborted).toBe(true)
  })

  it('send를 다시 호출하면 이전 요청을 abort한다', async () => {
    let capturedFirstSignal: AbortSignal | undefined
    chatStreamMock.mockImplementationOnce((_m: unknown, _t: unknown, signal: AbortSignal) => {
      capturedFirstSignal = signal
      return new Promise<Response>(() => {})
    })
    chatStreamMock.mockResolvedValueOnce(makeSseResponse(['data: [DONE]\n\n']))

    const { result } = renderHook(() => useSSEChat())
    const callbacks = makeCallbacks()

    act(() => {
      void result.current.send([], 'general_english', callbacks)
    })
    await vi.waitFor(() => expect(capturedFirstSignal).toBeDefined())

    await act(async () => {
      await result.current.send([], 'general_english', makeCallbacks())
    })

    expect(capturedFirstSignal!.aborted).toBe(true)
  })
})
