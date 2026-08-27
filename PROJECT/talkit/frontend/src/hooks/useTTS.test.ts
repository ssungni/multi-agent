import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTTS } from './useTTS'

const { ttsMock } = vi.hoisted(() => ({ ttsMock: vi.fn() }))

vi.mock('@/services/conversationApi', () => ({
  conversationApi: { tts: ttsMock },
}))

function makeBlob(): Blob {
  const blob = new Blob(['audio'])
  if (!blob.arrayBuffer) {
    ;(blob as unknown as { arrayBuffer: () => Promise<ArrayBuffer> }).arrayBuffer = () =>
      Promise.resolve(new ArrayBuffer(8))
  }
  return blob
}

describe('useTTS', () => {
  beforeEach(() => {
    ttsMock.mockReset()
  })

  it('빈 텍스트는 tts API를 호출하지 않는다', async () => {
    const { result } = renderHook(() => useTTS())
    act(() => {
      result.current.initQueue({})
    })

    await act(async () => {
      await result.current.enqueue('   ')
    })

    expect(ttsMock).not.toHaveBeenCalled()
  })

  it('enqueue(text)는 tts API를 호출하고 결과를 큐에 추가해 재생을 시작시킨다', async () => {
    ttsMock.mockResolvedValue(makeBlob())
    const onPlaybackStart = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onPlaybackStart })
    })

    await act(async () => {
      await result.current.enqueue('Hello world')
    })

    expect(ttsMock).toHaveBeenCalledWith('Hello world', expect.any(AbortSignal))
    expect(onPlaybackStart).toHaveBeenCalledWith('blob:mock-url')
  })

  it('speak은 enqueue의 별칭이다', () => {
    const { result } = renderHook(() => useTTS())
    expect(result.current.speak).toBe(result.current.enqueue)
  })

  it('tts API가 실패하면 initQueue에 전달된 onError가 호출된다', async () => {
    ttsMock.mockRejectedValue(new Error('network down'))
    const onError = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onError })
    })

    await act(async () => {
      await result.current.enqueue('Hello')
    })

    expect(onError).toHaveBeenCalledTimes(1)
    expect((onError.mock.calls[0]![0] as Error).message).toBe('network down')
  })

  it('이미 다른 문장이 재생 중이면, 한 문장의 TTS 실패는 onError를 호출하지 않고 조용히 건너뛴다', async () => {
    ttsMock
      .mockResolvedValueOnce(makeBlob()) // 문장 1: 성공
      .mockRejectedValueOnce(new Error('sentence 2 failed')) // 문장 2: 실패
    const onError = vi.fn()
    const onPlaybackStart = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onError, onPlaybackStart })
    })

    await act(async () => {
      await result.current.enqueue('Sentence one.')
    })
    await act(async () => {
      await result.current.enqueue('Sentence two?')
    })

    expect(onPlaybackStart).toHaveBeenCalledTimes(1) // 문장 1은 정상 재생
    expect(onError).not.toHaveBeenCalled() // 문장 2 실패만으로 전체 턴을 에러로 만들지 않음
  })

  it('이번 턴의 유일한 문장이 실패하면(아무것도 재생되지 않음) onError를 호출한다', async () => {
    ttsMock.mockRejectedValue(new Error('only sentence failed'))
    const onError = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onError })
    })

    await act(async () => {
      await result.current.enqueue('The only sentence.')
    })

    expect(onError).toHaveBeenCalledTimes(1)
  })

  it('AbortError는 onError를 호출하지 않는다', async () => {
    ttsMock.mockRejectedValue(new DOMException('aborted', 'AbortError'))
    const onError = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onError })
    })

    await act(async () => {
      await result.current.enqueue('Hello')
    })

    expect(onError).not.toHaveBeenCalled()
  })

  it('stop() 이후 도착한 tts 응답은 큐에 추가되지 않는다 (signal already aborted)', async () => {
    let resolveTts!: (blob: Blob) => void
    ttsMock.mockImplementation(
      () =>
        new Promise<Blob>((resolve) => {
          resolveTts = resolve
        })
    )
    const onPlaybackStart = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onPlaybackStart })
    })

    let enqueuePromise!: Promise<void>
    act(() => {
      enqueuePromise = result.current.enqueue('Hello')
    })

    act(() => {
      result.current.stop()
    })

    await act(async () => {
      resolveTts(makeBlob())
      await enqueuePromise
    })

    expect(onPlaybackStart).not.toHaveBeenCalled()
  })

  it('initQueue를 다시 호출하면 이전 턴의 진행 중 요청을 abort한다', async () => {
    let resolveTts!: (blob: Blob) => void
    ttsMock.mockImplementation(
      () =>
        new Promise<Blob>((resolve) => {
          resolveTts = resolve
        })
    )
    const firstOnPlaybackStart = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onPlaybackStart: firstOnPlaybackStart })
    })

    let enqueuePromise!: Promise<void>
    act(() => {
      enqueuePromise = result.current.enqueue('first turn text')
    })

    // 새 턴 시작 — 이전 턴의 AbortController를 abort시킴
    act(() => {
      result.current.initQueue({})
    })

    await act(async () => {
      resolveTts(makeBlob())
      await enqueuePromise
    })

    expect(firstOnPlaybackStart).not.toHaveBeenCalled()
  })

  it('문장 1 재생이 끝났을 때 문장 2의 TTS 응답이 아직 도착하지 않았으면 onQueueEmpty를 너무 일찍 호출하지 않는다', async () => {
    // 이 테스트 전용 AudioContext mock — source.onended를 직접 트리거하기 위해 직접 만든다.
    const sources: Array<{ onended: (() => void) | null }> = []
    const mockCtx = {
      state: 'running',
      destination: {},
      createBufferSource: vi.fn(() => {
        const source = { onended: null as (() => void) | null, start: vi.fn(), stop: vi.fn(), buffer: null, connect: vi.fn() }
        sources.push(source)
        return source
      }),
      decodeAudioData: vi.fn(() => Promise.resolve({} as AudioBuffer)),
      resume: vi.fn(() => Promise.resolve()),
      close: vi.fn(() => Promise.resolve()),
    }
    vi.stubGlobal('AudioContext', vi.fn(() => mockCtx))

    let resolveSecond!: (blob: Blob) => void
    ttsMock
      .mockResolvedValueOnce(makeBlob())
      .mockImplementationOnce(
        () =>
          new Promise<Blob>((resolve) => {
            resolveSecond = resolve
          })
      )

    const onQueueEmpty = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onQueueEmpty })
    })

    // 문장 1 — 즉시 resolve되어 재생이 바로 시작된다
    await act(async () => {
      await result.current.enqueue('Sentence one.')
    })

    // 문장 2 — fetch가 아직 끝나지 않은 상태 (resolveSecond 호출 전)
    let secondEnqueuePromise!: Promise<void>
    act(() => {
      secondEnqueuePromise = result.current.enqueue('Sentence two?')
    })

    // 문장 1의 재생이 끝났다고 시뮬레이션 — 이 시점에 문장 2는 아직 도착 전이다
    act(() => {
      sources[0]!.onended?.()
    })

    // 문장 2가 아직 안 왔으므로 대화가 끝난 게 아니다 — onQueueEmpty가 호출되면 안 된다
    expect(onQueueEmpty).not.toHaveBeenCalled()

    // 문장 2의 fetch가 도착 → 재생 시작
    await act(async () => {
      resolveSecond(makeBlob())
      await secondEnqueuePromise
    })
    expect(onQueueEmpty).not.toHaveBeenCalled() // 아직 재생 중

    // 문장 2 재생도 끝남 → 이제는 진짜로 끝난 것이 맞다
    act(() => {
      sources[1]!.onended?.()
    })
    expect(onQueueEmpty).toHaveBeenCalledTimes(1)
  })

  it('문장 2의 TTS 응답이 문장 1보다 먼저 도착해도, 재생은 문장 1부터 순서대로 시작한다', async () => {
    const sources: Array<{ onended: (() => void) | null }> = []
    const mockCtx = {
      state: 'running',
      destination: {},
      createBufferSource: vi.fn(() => {
        const source = { onended: null as (() => void) | null, start: vi.fn(), stop: vi.fn(), buffer: null, connect: vi.fn() }
        sources.push(source)
        return source
      }),
      decodeAudioData: vi.fn(() => Promise.resolve({} as AudioBuffer)),
      resume: vi.fn(() => Promise.resolve()),
      close: vi.fn(() => Promise.resolve()),
    }
    vi.stubGlobal('AudioContext', vi.fn(() => mockCtx))

    let resolveFirst!: (blob: Blob) => void
    ttsMock.mockImplementationOnce(
      () =>
        new Promise<Blob>((resolve) => {
          resolveFirst = resolve
        })
    )
    ttsMock.mockResolvedValueOnce(makeBlob()) // 문장 2가 먼저 끝남

    const onPlaybackStart = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onPlaybackStart })
    })

    let firstPromise!: Promise<void>
    act(() => {
      firstPromise = result.current.enqueue('Sentence one.')
    })

    // 문장 2의 네트워크 응답이 문장 1보다 먼저 도착한다
    await act(async () => {
      await result.current.enqueue('Sentence two?')
    })

    // 문장 2가 먼저 도착했어도, 문장 1이 아직 안 왔으므로 재생은 시작되지 않아야 한다
    expect(onPlaybackStart).not.toHaveBeenCalled()

    // 이제서야 문장 1의 응답이 도착 — 그제서야 문장 1부터 재생이 시작되어야 한다
    await act(async () => {
      resolveFirst(makeBlob())
      await firstPromise
    })

    expect(onPlaybackStart).toHaveBeenCalledTimes(1)

    act(() => {
      sources[0]!.onended?.()
    })

    // 문장 1이 끝난 뒤에야 문장 2가 이어서 재생된다 — 응답 도착 순서가 아니라 문장 순서대로
    expect(onPlaybackStart).toHaveBeenCalledTimes(2)
  })

  it('destroy()는 큐를 파괴하고 이후 재생을 시작시키지 않는다', async () => {
    ttsMock.mockResolvedValue(makeBlob())
    const onPlaybackStart = vi.fn()
    const { result } = renderHook(() => useTTS())

    act(() => {
      result.current.initQueue({ onPlaybackStart })
    })
    act(() => {
      result.current.destroy()
    })

    await act(async () => {
      await result.current.enqueue('Hello')
    })

    expect(onPlaybackStart).not.toHaveBeenCalled()
  })
})
