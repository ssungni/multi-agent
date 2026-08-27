// 문장 단위로 들어오는 LLM 응답을 순서대로 TTS 변환 후 재생 큐에 넣는 훅
import { useRef, useCallback, useMemo } from 'react'
import { conversationApi } from '@/services/conversationApi'
import { AudioQueue } from '@/lib/audioQueue'
import type { AudioQueueOptions } from '@/lib/audioQueue'

export function useTTS() {
  const queueRef = useRef<AudioQueue | null>(null)
  const turnAbortRef = useRef(new AbortController())
  // Stores the error handler set by initQueue so API errors are surfaced correctly
  const onErrorRef = useRef<(err: Error) => void>(() => {})
  const onQueueEmptyRef = useRef<() => void>(() => {})
  // 문장 단위로 TTS를 병렬 요청하다 보면, 앞 문장이 다 재생된 시점에 다음 문장의
  // 네트워크 요청이 아직 안 끝나 있을 수 있다. AudioQueue 내부의 pendingEnqueues는
  // "fetch가 끝나고 AudioQueue.enqueue가 호출된 이후"만 알기 때문에, 그 이전(네트워크
  // 응답 대기 중) 구간을 여기서 직접 세어 onQueueEmpty가 너무 일찍 불리는 걸 막는다.
  // (이게 없으면 다음 문장이 도착하기 전에 "대화 끝"으로 처리되어 마이크가 자동으로
  // 켜지고, 그 때 tts.stop()이 아직 도착 중이던 다음 문장 요청을 취소해버린다.)
  const pendingFetchesRef = useRef(0)
  // 문장별로 매겨지는 재생 순서 — enqueue가 "호출된" 순서를 보장한다
  // (응답이 도착하는 순서가 아니라). AudioQueue가 이 index를 기준으로 정렬해 재생한다.
  const nextIndexRef = useRef(0)
  // 이번 턴에서 큐에 성공적으로 들어간 문장이 하나라도 있는지 — 한 문장의 TTS 실패가
  // 전체 턴을 에러로 만들지 않도록, "이번 턴에 재생할 수 있는 게 정말 하나도 없을 때"만
  // onError를 표면화하는 데 쓴다 (그 외에는 그 문장만 건너뛰고 나머지는 계속 재생).
  const hasPlayableAudioRef = useRef(false)

  // 새 대화 턴을 시작할 때 큐와 관련 상태를 모두 초기화하고 새 AudioQueue를 생성
  const initQueue = useCallback((opts: AudioQueueOptions) => {
    onErrorRef.current = opts.onError ?? (() => {})
    onQueueEmptyRef.current = opts.onQueueEmpty ?? (() => {})
    pendingFetchesRef.current = 0
    nextIndexRef.current = 0
    hasPlayableAudioRef.current = false
    turnAbortRef.current.abort()
    turnAbortRef.current = new AbortController()
    queueRef.current?.destroy()
    queueRef.current = new AudioQueue({
      ...opts,
      onQueueEmpty: () => {
        if (pendingFetchesRef.current === 0) onQueueEmptyRef.current()
      },
    })
  }, [])

  // Fetch TTS audio and add to the playback queue.
  // Errors (other than AbortError) are forwarded to onError so fire-and-forget
  // callers (`void tts.enqueue(...)`) don't create unhandled rejections.
  const enqueue = useCallback(async (text: string) => {
    if (!text.trim()) return
    const index = nextIndexRef.current++
    const signal = turnAbortRef.current.signal
    pendingFetchesRef.current++
    try {
      const blob = await conversationApi.tts(text, signal)
      if (signal.aborted) {
        // 중단된 요청도 자리를 채워둬야 뒤(늦게 끝난) index가 영원히 대기하지 않는다.
        queueRef.current?.skip(index)
      } else {
        await queueRef.current?.enqueue(index, blob)
        hasPlayableAudioRef.current = true
      }
    } catch (err) {
      queueRef.current?.skip(index)
      if ((err as { name?: string }).name !== 'AbortError') {
        // 이 요청이 이번 턴의 마지막 대기 항목인데 그동안 단 한 문장도 재생되지
        // 못했다면(예: 응답이 한 문장뿐이었는데 그게 실패함) 사용자가 아무 소리도
        // 듣지 못한 채 방치되므로 그때만 에러를 표면화한다. 다른 문장이 이미 재생
        // 중이거나 아직 응답을 기다리는 중이면, 이 문장만 건너뛰고 조용히 계속한다.
        if (!hasPlayableAudioRef.current && pendingFetchesRef.current === 1) {
          onErrorRef.current(err as Error)
        }
      }
    } finally {
      pendingFetchesRef.current--
      // 이 요청이 마지막으로 남아있던 대기 항목이었는데, 그동안 AudioQueue 재생이
      // 이미 끝나 있었을 수 있다 — 다시 한번 비어있는지 확인해서 놓치지 않게 한다.
      if (pendingFetchesRef.current === 0) queueRef.current?.recheckEmpty()
    }
  }, [])

  // 현재 턴의 모든 진행 중인 요청과 재생을 즉시 중단
  const stop = useCallback(() => {
    turnAbortRef.current.abort()
    queueRef.current?.stop()
  }, [])

  // 큐를 완전히 폐기 — 컴포넌트 unmount 등 더 이상 재사용하지 않을 때 호출
  const destroy = useCallback(() => {
    turnAbortRef.current.abort()
    queueRef.current?.destroy()
    queueRef.current = null
  }, [])

  // 반환 객체 자체를 안정된 참조로 고정한다 — 그렇지 않으면 이 훅을 쓰는 쪽에서
  // (예: useConversation의 startOpening/startRecording) 매 렌더링마다 새 객체를
  // 의존성으로 받아 콜백이 다시 만들어지고, 그 콜백에 의존하는 effect(자동 녹음
  // 시작 등)가 의도치 않게 더 자주 재실행되어 타이밍 버그를 일으킨다.
  return useMemo(
    () => ({ initQueue, speak: enqueue, enqueue, stop, destroy }),
    [initQueue, enqueue, stop, destroy]
  )
}
