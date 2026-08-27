import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AudioQueue } from './audioQueue'

// blob.arrayBuffer()는 jsdom Blob에 구현되어 있지 않을 수 있으므로 안전하게 스텁한다.
function makeBlob(): Blob {
  const blob = new Blob(['fake-audio-bytes'])
  if (!blob.arrayBuffer) {
    ;(blob as unknown as { arrayBuffer: () => Promise<ArrayBuffer> }).arrayBuffer = () =>
      Promise.resolve(new ArrayBuffer(8))
  }
  return blob
}

describe('AudioQueue', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('enqueue 시 onPlaybackStart가 blobUrl과 함께 호출된다', async () => {
    const onPlaybackStart = vi.fn()
    const queue = new AudioQueue({ onPlaybackStart })

    await queue.enqueue(0, makeBlob())

    expect(onPlaybackStart).toHaveBeenCalledWith('blob:mock-url')
  })

  it('재생할 audio가 모두 끝나면 onQueueEmpty가 호출된다', async () => {
    const onQueueEmpty = vi.fn()
    const queue = new AudioQueue({ onQueueEmpty })

    await queue.enqueue(0, makeBlob())
    expect(onQueueEmpty).not.toHaveBeenCalled()

    // AudioContext.createBufferSource()가 만든 source의 onended를 직접 트리거해 재생 종료를 시뮬레이션
    const ctx = (queue as unknown as { ctx: AudioContext }).ctx
    const source = vi.mocked(ctx.createBufferSource).mock.results[0]!.value as {
      onended: (() => void) | null
    }
    source.onended?.()

    expect(onQueueEmpty).toHaveBeenCalledTimes(1)
  })

  it('두 번째 블록이 재생 중에 도착하면 순서대로 재생되고, 모두 끝난 뒤에만 onQueueEmpty가 호출된다', async () => {
    const onPlaybackStart = vi.fn()
    const onQueueEmpty = vi.fn()
    const queue = new AudioQueue({ onPlaybackStart, onQueueEmpty })

    await queue.enqueue(0, makeBlob())
    await queue.enqueue(1, makeBlob())

    expect(onPlaybackStart).toHaveBeenCalledTimes(1) // 두 번째는 큐에 대기 중, 아직 재생 시작 안 함

    const ctx = (queue as unknown as { ctx: AudioContext }).ctx
    const firstSource = vi.mocked(ctx.createBufferSource).mock.results[0]!.value as {
      onended: (() => void) | null
    }
    firstSource.onended?.()

    expect(onPlaybackStart).toHaveBeenCalledTimes(2)
    expect(onQueueEmpty).not.toHaveBeenCalled()

    const secondSource = vi.mocked(ctx.createBufferSource).mock.results[1]!.value as {
      onended: (() => void) | null
    }
    secondSource.onended?.()

    expect(onQueueEmpty).toHaveBeenCalledTimes(1)
  })

  it('index 1이 index 0보다 먼저 도착해도, index 0이 도착하기 전까지는 재생을 시작하지 않는다', async () => {
    const onPlaybackStart = vi.fn()
    const queue = new AudioQueue({ onPlaybackStart })

    // 응답이 늦게 끝난 문장(index 1)이 먼저 도착한 상황을 시뮬레이션
    await queue.enqueue(1, makeBlob())
    expect(onPlaybackStart).not.toHaveBeenCalled()

    // 그제서야 index 0이 도착 — 이제 0번부터 순서대로 재생되어야 한다
    const ctx = (queue as unknown as { ctx: AudioContext }).ctx
    await queue.enqueue(0, makeBlob())

    expect(onPlaybackStart).toHaveBeenCalledTimes(1)

    const firstSource = vi.mocked(ctx.createBufferSource).mock.results[0]!.value as {
      onended: (() => void) | null
    }
    firstSource.onended?.()

    // index 0 재생이 끝나야 비로소 index 1이 이어서 재생된다
    expect(onPlaybackStart).toHaveBeenCalledTimes(2)
  })

  it('skip()으로 건너뛴 index는 재생되지 않지만, 그 뒤(다음 index)는 정상적으로 재생된다', async () => {
    const onPlaybackStart = vi.fn()
    const onQueueEmpty = vi.fn()
    const queue = new AudioQueue({ onPlaybackStart, onQueueEmpty })

    // index 1의 응답이 먼저 도착해 대기 중이다가, 그 뒤 index 0의 요청이 중단/실패로 skip된다
    await queue.enqueue(1, makeBlob())
    queue.skip(0)

    expect(onPlaybackStart).toHaveBeenCalledTimes(1)
    expect(onPlaybackStart).toHaveBeenCalledWith('blob:mock-url')

    const ctx = (queue as unknown as { ctx: AudioContext }).ctx
    const source = vi.mocked(ctx.createBufferSource).mock.results[0]!.value as {
      onended: (() => void) | null
    }
    source.onended?.()

    expect(onQueueEmpty).toHaveBeenCalledTimes(1)
  })

  it('recheckEmpty()는 큐가 비어있고 재생 중이 아닐 때 onQueueEmpty를 호출한다', async () => {
    const onQueueEmpty = vi.fn()
    const queue = new AudioQueue({ onQueueEmpty })

    queue.recheckEmpty()

    expect(onQueueEmpty).toHaveBeenCalledTimes(1)
  })

  it('recheckEmpty()는 재생 중일 때는 onQueueEmpty를 호출하지 않는다', async () => {
    const onQueueEmpty = vi.fn()
    const queue = new AudioQueue({ onQueueEmpty })

    await queue.enqueue(0, makeBlob())
    queue.recheckEmpty()

    expect(onQueueEmpty).not.toHaveBeenCalled()
  })

  it('decodeAudioData가 실패하면 onError가 호출되고 onQueueEmpty도 함께 호출된다', async () => {
    const onError = vi.fn()
    const onQueueEmpty = vi.fn()
    const queue = new AudioQueue({ onError, onQueueEmpty })

    // 다음 AudioContext 인스턴스의 decodeAudioData가 실패하도록 설정
    const ctx = new AudioContext()
    vi.mocked(ctx.decodeAudioData).mockRejectedValueOnce(new Error('decode failed'))
    vi.stubGlobal(
      'AudioContext',
      vi.fn(() => ctx)
    )

    await queue.enqueue(0, makeBlob())

    expect(onError).toHaveBeenCalledTimes(1)
    expect((onError.mock.calls[0]![0] as Error).message).toBe('decode failed')
    expect(onQueueEmpty).toHaveBeenCalledTimes(1)
  })

  it('stop()은 큐를 비우고 현재 재생 중인 source를 정지시킨다', async () => {
    const queue = new AudioQueue()
    await queue.enqueue(0, makeBlob())

    const ctx = (queue as unknown as { ctx: AudioContext }).ctx
    const source = vi.mocked(ctx.createBufferSource).mock.results[0]!.value as { stop: () => void }

    queue.stop()

    expect(source.stop).toHaveBeenCalledTimes(1)
  })

  it('stop()이 source.stop()의 예외를 무시한다', async () => {
    const queue = new AudioQueue()
    await queue.enqueue(0, makeBlob())

    const ctx = (queue as unknown as { ctx: AudioContext }).ctx
    const source = vi.mocked(ctx.createBufferSource).mock.results[0]!.value as {
      stop: () => void
    }
    vi.mocked(source.stop).mockImplementation(() => {
      throw new Error('already stopped')
    })

    expect(() => queue.stop()).not.toThrow()
  })

  it('destroy()는 stop()을 호출하고 AudioContext를 닫는다', async () => {
    const queue = new AudioQueue()
    await queue.enqueue(0, makeBlob())

    const ctx = (queue as unknown as { ctx: AudioContext }).ctx

    queue.destroy()

    expect(ctx.close).toHaveBeenCalledTimes(1)
  })
})
