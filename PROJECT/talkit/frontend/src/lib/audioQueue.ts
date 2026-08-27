// TTS로 생성된 오디오 조각들을 순서대로 디코딩/재생하는 큐.
export interface AudioQueueOptions {
  onPlaybackStart?: (blobUrl: string) => void
  onQueueEmpty?: () => void
  onError?: (err: Error) => void
}

type QueueItem = { buffer: AudioBuffer; blobUrl: string }

export class AudioQueue {
  private ctx: AudioContext | null = null
  private queue: QueueItem[] = []
  private isPlaying = false
  private currentSource: AudioBufferSourceNode | null = null
  private pendingEnqueues = 0
  private opts: AudioQueueOptions

  // 문장 단위로 TTS를 병렬 요청하면 네트워크 응답이 원래 문장 순서와 다르게
  // 도착할 수 있다 (예: 두 번째 문장이 첫 번째보다 먼저 끝남). 그래서 도착한
  // 순서가 아니라 index 순서대로만 재생 큐에 올린다 — 더 앞선 index가 아직
  // 안 왔으면, 늦게 온 뒷 index는 여기서 대기시킨다.
  private pendingItems = new Map<number, QueueItem | null>()
  private nextPlayIndex = 0

  constructor(opts: AudioQueueOptions = {}) {
    this.opts = opts
  }

  // index번째 문장의 오디오 blob을 디코딩해서 도착 대기열(pendingItems)에 등록한다.
  async enqueue(index: number, blob: Blob): Promise<void> {
    this.pendingEnqueues++
    try {
      if (!this.ctx) this.ctx = new AudioContext()
      // 브라우저 정책상 AudioContext가 suspended 상태로 생성될 수 있어 재생 전 resume이 필요하다.
      if (this.ctx.state === 'suspended') await this.ctx.resume()
      const arrayBuffer = await blob.arrayBuffer()
      const audioBuffer = await this.ctx.decodeAudioData(arrayBuffer)
      const blobUrl = URL.createObjectURL(blob)
      this.pendingItems.set(index, { buffer: audioBuffer, blobUrl })
    } catch (err) {
      this.pendingEnqueues--
      this.opts.onError?.(err as Error)
      // 이 index는 재생할 수 없지만, 자리만은 채워서 뒤에 도착한 index들이
      // 영원히 대기하지 않게 한다.
      this.pendingItems.set(index, null)
      this.flushReady()
      return
    }
    this.pendingEnqueues--
    this.flushReady()
  }

  // 해당 index의 오디오를 영구히 건너뛴다 (요청이 중단되었거나 텍스트가 비어있던 경우).
  skip(index: number): void {
    this.pendingItems.set(index, null)
    this.flushReady()
  }

  // nextPlayIndex부터 순서대로 도착해 있는 항목들을 실제 재생 큐로 옮긴다.
  private flushReady(): void {
    while (this.pendingItems.has(this.nextPlayIndex)) {
      const item = this.pendingItems.get(this.nextPlayIndex)!
      this.pendingItems.delete(this.nextPlayIndex)
      if (item) this.queue.push(item)
      this.nextPlayIndex++
    }
    if (!this.isPlaying) this.playNext()
  }

  // 재생 큐에서 다음 항목을 꺼내 재생하고, 끝나면 자기 자신을 다시 호출해 체이닝한다.
  private playNext(): void {
    if (this.queue.length === 0) {
      this.isPlaying = false
      this.checkEmpty()
      return
    }
    this.isPlaying = true
    const item = this.queue.shift()!
    this.opts.onPlaybackStart?.(item.blobUrl)
    const source = this.ctx!.createBufferSource()
    source.buffer = item.buffer
    source.connect(this.ctx!.destination)
    source.onended = () => this.playNext()
    source.start(0)
    this.currentSource = source
  }

  // 외부(useTTS)에서 추적하는 "아직 응답이 안 온 요청"이 0이 된 직후 호출된다.
  // 그 사이에 재생이 이미 끝나 있었을 수 있으므로 다시 한번 비어있는지 확인한다.
  recheckEmpty(): void {
    this.checkEmpty()
  }

  // 대기/재생 중인 항목이 전혀 없을 때만 onQueueEmpty를 호출하기 위한 조건 검사.
  private checkEmpty(): void {
    if (
      this.pendingEnqueues === 0 &&
      this.pendingItems.size === 0 &&
      this.queue.length === 0 &&
      !this.isPlaying
    ) {
      this.opts.onQueueEmpty?.()
    }
  }

  // 재생 중인 오디오를 즉시 멈추고 큐 상태를 전부 초기화한다 (예: 사용자가 대화를 중단할 때).
  stop(): void {
    this.queue = []
    this.isPlaying = false
    this.pendingEnqueues = 0
    this.pendingItems.clear()
    this.nextPlayIndex = 0
    if (this.currentSource) {
      try {
        // 이미 정지된 source에서 stop()을 다시 호출하면 예외가 발생할 수 있어 무시한다.
        this.currentSource.stop()
      } catch {}
      this.currentSource = null
    }
  }

  // 컴포넌트 unmount 등으로 더 이상 큐를 사용하지 않을 때 AudioContext까지 정리한다.
  destroy(): void {
    this.stop()
    void this.ctx?.close()
    this.ctx = null
  }
}
