// AI와의 대화 전체 흐름(오프닝 멘트 → 녹음 → STT → LLM 스트리밍 → TTS 재생, 재시도/취소 포함)을 관리하는 훅
import { useState, useCallback, useEffect, useRef } from 'react'
import { useConversationStore } from '@/stores/conversationStore'
import { useUserStore } from '@/stores/userStore'
import { conversationApi } from '@/services/conversationApi'
import { isNetworkError } from '@/lib/networkError'
import { trimSilence } from '@/lib/vad'
import { SESSION_HARD_LIMIT_MS } from '@/lib/constants'
import { useAudioRecorder } from './useAudioRecorder'
import { useSSEChat } from './useSSEChat'
import { useTTS } from './useTTS'
import type { ConversationMode } from '@/types/conversation'

const NETWORK_ERROR_MESSAGE = '네트워크 연결 오류. 인터넷 연결을 확인해주세요.'

// AI 튜터(관심사 기반 자유대화)는 명시적 topic_id가 없으므로, 매번 같은 문구 대신
// 시간대에 맞는 인사로 자연스럽게 시작한다 (서버 호출 없이 즉시 계산 — latency 없음).
// 시간대별로 여러 변형을 두고 매번 랜덤하게 골라, 매 대화가 같은 문장으로 시작되지 않게 한다.
const DAWN_OPENINGS = [
  "You're up early! Did you sleep well?",
  "You're up early! What are you doing this morning?",
  "You're up early! Are you starting your day already?",
  "You're up early! Do you usually wake up this early?",
  "Couldn't sleep? What's keeping you awake?",
  "Couldn't sleep? Have you been busy lately?",
  "Couldn't sleep? What are you doing right now?",
  "Couldn't sleep? Are you planning to stay awake for a while?",
]

const MORNING_OPENINGS = [
  'Good morning! Did you sleep well?',
  'Good morning! Have you had breakfast yet?',
  'Good morning! What did you have for breakfast?',
  'Good morning! What are your plans for today?',
  'Good morning! Do you have a busy day ahead?',
  'Good morning! What are you working on today?',
  "Good morning! How's your morning going so far?",
  'Good morning! Did you do anything interesting yesterday?',
]

const AFTERNOON_OPENINGS = [
  'Good afternoon! Have you had lunch yet?',
  'Good afternoon! What did you have for lunch?',
  "Good afternoon! How's your day going so far?",
  'Good afternoon! What are you doing right now?',
  "Hi! How's your afternoon going?",
  'Hi! Are you staying busy today?',
  'Hey! What are you working on at the moment?',
  'Hey! Is your work or study going well today?',
]

const EVENING_OPENINGS = [
  'Good evening! Have you had dinner yet?',
  'Good evening! What did you have for dinner?',
  'Good evening! How was your day?',
  'Good evening! Have you finished work for the day?',
  "How's your evening? Do you have any plans tonight?",
  "How's your evening? What are you doing right now?",
  "How's your evening? Are you relaxing after work or school?",
  "How's your evening? Did anything interesting happen today?",
]

const NIGHT_OPENINGS = [
  'Hi! What are you doing to relax tonight?',
  'Hi! Are you watching anything interesting right now?',
  'Hi! How was your day overall?',
  'Hi! What was the best part of your day?',
  'Hey! Are you watching YouTube or a movie tonight?',
  'Hey! What are you doing before bed?',
  'Hey! Do you usually stay up this late?',
  'Hey! Did anything memorable happen today?',
]

const LATE_NIGHT_OPENINGS = [
  "You're still awake? What are you doing up this late?",
  "You're still awake? Are you studying or working on something?",
  "You're still awake? Do you usually stay up this late?",
  "You're still awake? Are you a night owl?",
  "Can't sleep? What's on your mind?",
  "Can't sleep? Have you been having trouble sleeping lately?",
  "Can't sleep? What have you been doing tonight?",
  "Can't sleep? Are you planning to get some rest soon?",
]

function pickRandom(options: string[]): string {
  return options[Math.floor(Math.random() * options.length)]!
}

function timeOfDayOpening(): string {
  const hour = new Date().getHours()
  if (hour >= 4 && hour < 6) return pickRandom(DAWN_OPENINGS)
  if (hour >= 6 && hour < 12) return pickRandom(MORNING_OPENINGS)
  if (hour >= 12 && hour < 17) return pickRandom(AFTERNOON_OPENINGS)
  if (hour >= 17 && hour < 21) return pickRandom(EVENING_OPENINGS)
  if (hour >= 21 && hour < 24) return pickRandom(NIGHT_OPENINGS)
  return pickRandom(LATE_NIGHT_OPENINGS)
}

// 실전 모드(live) + 롤플레이면 힌트 없이 인캐릭터 대사로, 그 외(연습 모드, 또는
// 일반 AI 튜터 자유대화)는 기존처럼 힌트/시간대 인사로 시작한다.
// 롤플레이 시나리오의 오프닝 대사는 백엔드(Ai::ChatService::TOPICS)가 단일 진실
// 공급원이며, RoleplayPage → ChatPage를 거쳐 store에 그대로 전달된 값을 쓴다
// (LLM 호출 없이 즉시 TTS만으로 시작하기 위한 지연 최적화는 그대로 유지).
function openingFor(
  mode: ConversationMode,
  scenarioOpening: string | null,
  scenarioLiveOpening: string | null
): string {
  if (mode === 'live' && scenarioLiveOpening) return scenarioLiveOpening
  return scenarioOpening ?? timeOfDayOpening()
}

type RetryTarget =
  | { type: 'stt'; audioBlob: Blob }
  | { type: 'llm'; history: Array<{ role: string; content: string }>; wrapUp: boolean }

// 세션이 30분 한도를 넘었는지 store에서 직접 읽어 확인한다 (React 상태로 들고
// 다닐 필요 없이, 턴을 보낼 때마다 그 시점의 값을 바로 확인하면 충분하다).
function isSessionOverLimit(): boolean {
  const startedAt = useConversationStore.getState().sessionStartedAt
  if (!startedAt) return false
  return Date.now() - startedAt >= SESSION_HARD_LIMIT_MS
}

export function useConversation() {
  const {
    status,
    messages,
    streamingContent,
    error,
    setStatus,
    addMessage,
    appendStreamDelta,
    commitStreamMessage,
    clearStreaming,
    setError,
    addAudioUrl,
    setTopicId,
    setScenarioOpenings,
    markSessionStarted,
    reset,
  } = useConversationStore()
  const { userId } = useUserStore()

  const recorder = useAudioRecorder()
  const sseChat = useSSEChat()
  const tts = useTTS()

  const [activeStream, setActiveStream] = useState<MediaStream | null>(null)
  const [canRetry, setCanRetry] = useState(false)
  const [isMuted, setIsMuted] = useState(false)

  const aiMsgIdRef = useRef<string | null>(null)
  const sttAbortRef = useRef<AbortController | null>(null)
  const retryRef = useRef<RetryTarget | null>(null)
  // 직전(또는 진행 중)에 보낸 턴이 "마무리 턴"이었는지 — ChatPage가 이 턴의 TTS가 끝난
  // 뒤 자동 재녹음 대신 통화를 강제 종료할지 판단하는 데 쓴다.
  const isWrapUpTurnRef = useRef(false)

  // ─── Shared LLM turn ───────────────────────────────────────────────────────
  // Extracted so both stopRecording and retry can call it.
  const runLLMTurn = useCallback(
    async (history: Array<{ role: string; content: string }>, wrapUp = false) => {
      isWrapUpTurnRef.current = wrapUp
      const aiMsgId = crypto.randomUUID()
      aiMsgIdRef.current = aiMsgId
      clearStreaming()

      tts.initQueue({
        onPlaybackStart: (blobUrl) => addAudioUrl(aiMsgId, blobUrl),
        onQueueEmpty: () => setStatus('idle'),
        onError: () => setError('TTS 재생 실패'),
      })

      setStatus('llm_streaming')
      const { topicId, mode } = useConversationStore.getState()

      // Track TTS enqueue count so we know whether to wait for onQueueEmpty
      let ttsSentCount = 0

      await sseChat.send(
        history,
        topicId,
        {
          onDelta: (delta) => appendStreamDelta(delta),

          // Fires for every complete sentence during streaming → parallel TTS
          onSentence: (sentence) => {
            ttsSentCount++
            void tts.enqueue(sentence)
          },

          // Fires once when stream ends with any trailing text
          onDone: (remainder) => {
            const hasRemainder = remainder.length > 0
            if (hasRemainder) {
              ttsSentCount++
              void tts.enqueue(remainder)
            }

            commitStreamMessage(aiMsgId)

            if (ttsSentCount > 0) {
              // AudioQueue will call onQueueEmpty → setStatus('idle')
              setStatus('tts_playing')
            } else {
              // Nothing was sent to TTS (empty response)
              setStatus('idle')
            }
          },

          onError: (err) => {
            retryRef.current = { type: 'llm', history, wrapUp }
            setCanRetry(true)
            clearStreaming()
            setError(isNetworkError(err) ? NETWORK_ERROR_MESSAGE : 'AI 응답 실패. 다시 시도해주세요.')
          },
        },
        wrapUp,
        mode
      )
    },
    [
      sseChat,
      tts,
      appendStreamDelta,
      commitStreamMessage,
      clearStreaming,
      setStatus,
      setError,
      addAudioUrl,
    ]
  )

  // ─── AI opening ────────────────────────────────────────────────────────────
  // 대화 시작 시 토픽/시간대에 맞는 AI 오프닝 멘트를 즉시 추가하고 TTS로 재생
  const startOpening = useCallback(async () => {
    if (!userId) return
    const msgId = crypto.randomUUID()
    aiMsgIdRef.current = msgId
    isWrapUpTurnRef.current = false
    markSessionStarted()

    const { mode, scenarioOpening, scenarioLiveOpening } = useConversationStore.getState()
    const opening = openingFor(mode, scenarioOpening, scenarioLiveOpening)
    addMessage({ id: msgId, role: 'assistant', content: opening })
    setStatus('ai_opening')

    tts.initQueue({
      onPlaybackStart: (blobUrl) => addAudioUrl(msgId, blobUrl),
      onQueueEmpty: () => setStatus('idle'),
      onError: () => setStatus('idle'),
    })

    void tts.enqueue(opening)
  }, [userId, addMessage, setStatus, addAudioUrl, tts, markSessionStarted])

  // ─── Start recording ────────────────────────────────────────────────────────
  // status는 store에서 직접(getState) 읽는다 — React.StrictMode가 dev에서 effect를
  // 일부러 두 번 연달아 실행할 때, 같은 동기 구간 안에서 startOpening()이 store의
  // status를 'ai_opening'으로 바꿔도 이 콜백이 캡처해온 status 인자는 그 직전 렌더의
  // 값('idle')에 머물러 있을 수 있다. 그 stale 값을 보고 녹음을 시작해버리면 막
  // 시작된 TTS 요청을 tts.stop()이 취소해버려 인사말이 안 들리는 문제가 생긴다.
  const startRecording = useCallback(async () => {
    if (useConversationStore.getState().status !== 'idle') return
    tts.stop()

    try {
      const stream = await recorder.start()
      setIsMuted(false)
      setActiveStream(stream)
      setStatus('recording')
    } catch {
      setError('마이크 접근 실패. 브라우저 권한을 확인해주세요.')
    }
  }, [tts, recorder, setStatus, setError])

  // ─── 음소거 토글 ─────────────────────────────────────────────────────────────
  // 마이크 버튼 클릭은 더 이상 "답변 완료(전송)"를 의미하지 않는다 — 그냥 음소거를
  // 켜고 끌 뿐이다. MediaRecorder만 pause/resume해서, 음소거 구간의 오디오는 최종
  // 전송 blob에서 빠지고, 마이크 스트림 자체는 계속 열려있어 다시 켤 때 끊김이 없다.
  const toggleMute = useCallback(() => {
    if (status !== 'recording') return
    if (isMuted) {
      recorder.resume()
      setIsMuted(false)
    } else {
      recorder.pause()
      setIsMuted(true)
    }
  }, [status, isMuted, recorder])

  // ─── STT 결과 처리 → LLM 턴 시작 ────────────────────────────────────────────
  // stopRecording(최초 시도)과 retry의 STT 재시도가 동일한 흐름을 거치므로 추출했다:
  // STT 호출 → 빈 텍스트면 idle 복귀 → 메시지 추가 → history 구성 → LLM 턴 시작,
  // 실패 시 재시도 대상 등록.
  const runSttResult = useCallback(
    async (audioBlob: Blob, signal: AbortSignal) => {
      try {
        const { text } = await conversationApi.stt(audioBlob, signal)

        if (!text.trim()) {
          setStatus('idle')
          return
        }

        addMessage({
          id: crypto.randomUUID(),
          role: 'user',
          content: text,
          audioUrls: [URL.createObjectURL(audioBlob)],
        })

        const history = useConversationStore.getState().messages.map(({ role, content }) => ({
          role,
          content,
        }))

        // 세션이 30분 한도를 넘었으면, 이번 응답에서 AI가 자연스럽게 마무리하도록 한다.
        const wrapUp = isSessionOverLimit()
        retryRef.current = { type: 'llm', history, wrapUp }
        setCanRetry(false) // STT 단계는 끝났으니, 이전 STT 실패로 떠 있던 재시도 버튼을 정리
        await runLLMTurn(history, wrapUp)
      } catch (err) {
        if ((err as { name?: string }).name === 'AbortError') return
        retryRef.current = { type: 'stt', audioBlob }
        setCanRetry(true)
        setError(isNetworkError(err) ? NETWORK_ERROR_MESSAGE : '음성 인식 실패. 다시 시도해주세요.')
      }
    },
    [addMessage, setStatus, setError, runLLMTurn]
  )

  // ─── 답변 완료 → STT → LLM ──────────────────────────────────────────────────
  const stopRecording = useCallback(async () => {
    if (status !== 'recording') return
    setActiveStream(null)
    setIsMuted(false)
    setStatus('vad_processing')

    const rawBlob = await recorder.stop()
    if (!rawBlob.size) {
      setStatus('idle')
      return
    }

    // 유저가 실제로 말한 구간만 남기고 앞뒤 무음을 잘라낸다 — 전체가 무음이면
    // STT 요청 자체를 보내지 않는다 (Whisper 환각 방지 + 불필요한 요청 절약).
    const { blob: audioBlob, hadSpeech } = await trimSilence(rawBlob)
    if (!hadSpeech) {
      setStatus('idle')
      return
    }

    setStatus('stt_processing')
    const sttCtrl = new AbortController()
    sttAbortRef.current = sttCtrl
    await runSttResult(audioBlob, sttCtrl.signal)
  }, [status, recorder, setStatus, runSttResult])

  // ─── Cancel mid-stream ──────────────────────────────────────────────────────
  // 진행 중인 STT/LLM/TTS 요청을 모두 중단하고 idle 상태로 되돌림 (마이크 스트림은 유지)
  const cancel = useCallback(() => {
    sttAbortRef.current?.abort()
    sseChat.abort()
    tts.stop()
    clearStreaming()
    retryRef.current = null
    setCanRetry(false)
    setIsMuted(false)
    setStatus('idle')
  }, [sseChat, tts, clearStreaming, setStatus])

  // ─── End call (전화 끊기) ───────────────────────────────────────────────────
  // cancel()과 달리, 녹음 중이었다면 마이크 스트림 자체를 확실히 해제한다
  // (대화 종료 후에도 마이크가 켜진 상태로 남는 것을 방지).
  const endCall = useCallback(async () => {
    sttAbortRef.current?.abort()
    sseChat.abort()
    tts.stop()
    clearStreaming()
    retryRef.current = null
    setCanRetry(false)
    setIsMuted(false)
    if (status === 'recording') {
      setActiveStream(null)
      await recorder.stop()
    }
    setStatus('idle')
  }, [status, sseChat, tts, clearStreaming, setStatus, recorder])

  // ─── Retry last failed operation ────────────────────────────────────────────
  const retry = useCallback(async () => {
    const target = retryRef.current
    if (!target) return
    setCanRetry(false)
    clearStreaming()

    if (target.type === 'stt') {
      setStatus('stt_processing')
      const sttCtrl = new AbortController()
      sttAbortRef.current = sttCtrl
      await runSttResult(target.audioBlob, sttCtrl.signal)
    } else {
      // LLM retry: re-send with the same history snapshot (같은 wrapUp 결정도 유지)
      retryRef.current = target // keep in case retry also fails
      await runLLMTurn(target.history, target.wrapUp)
    }
  }, [clearStreaming, setStatus, runLLMTurn, runSttResult])

  // ─── Dismiss error (no retry) ───────────────────────────────────────────────
  const dismissError = useCallback(() => {
    retryRef.current = null
    setCanRetry(false)
    setStatus('idle')
  }, [setStatus])

  useEffect(
    () => () => {
      sseChat.abort()
      tts.destroy()
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  )

  return {
    status,
    messages,
    streamingContent,
    error,
    activeStream,
    canRetry,
    isMuted,
    isRecording: recorder.isRecording,
    setTopicId,
    setScenarioOpenings,
    startOpening,
    startRecording,
    stopRecording,
    toggleMute,
    cancel,
    endCall,
    retry,
    dismissError,
    reset,
    // 직전 턴이 "마무리 턴"이었는지 — 그 턴의 TTS가 끝난 뒤 자동 재녹음 대신
    // 통화를 강제 종료해야 하는지 ChatPage가 판단하는 데 쓴다. ref를 그대로 노출하는
    // 대신 함수로 감싸 호출 시점의 최신 값만 읽을 수 있게 한다.
    wasLastTurnWrapUp: () => isWrapUpTurnRef.current,
  }
}
