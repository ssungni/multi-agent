import { useEffect, useRef, useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { ArrowLeft, BookOpen, X, RotateCcw, Phone } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { MessageList } from '@/components/chat/MessageList'
import { Waveform } from '@/components/chat/Waveform'
import { AudioRecorder } from '@/components/chat/AudioRecorder'
import { ChatStatusBar } from '@/components/chat/ChatStatusBar'
import { EndConversationDialog } from '@/components/chat/EndConversationDialog'
import { ExtendConversationDialog } from '@/components/chat/ExtendConversationDialog'
import { useConversation } from '@/hooks/useConversation'
import { useSpeechWhileMuted } from '@/hooks/useSpeechWhileMuted'
import { useAutoStopOnSilence } from '@/hooks/useAutoStopOnSilence'
import { useMembershipQuery } from '@/hooks/queries/useMembershipQuery'
import { useUserStore } from '@/stores/userStore'
import { useConversationStore } from '@/stores/conversationStore'
import { formatDuration, countWords } from '@/lib/utils'
import { SESSION_HARD_LIMIT_MS } from '@/lib/constants'
import type { ConversationStatus } from '@/types/conversation'

// vad_processing/stt_processing 동안은 마이크 버튼이 ∅(비활성) 상태로 계속 보이므로
// 취소 버튼까지 같이 띄우면 중복돼 보인다 — AI가 응답을 만들고 말하는 동안만 취소를 노출한다.
const CANCELLABLE: ConversationStatus[] = ['ai_opening', 'llm_streaming', 'tts_playing']

// 5분마다 "연장하시겠습니까?"를 물어 대화를 계속할지 확인한다.
const EXTEND_PROMPT_INTERVAL_MS = 5 * 60 * 1000

export function ChatPage() {
  const { userId } = useUserStore()
  const navigate = useNavigate()
  const location = useLocation()
  const { data: membership, isLoading } = useMembershipQuery()

  const {
    status,
    messages,
    streamingContent,
    error,
    activeStream,
    canRetry,
    isMuted,
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
    wasLastTurnWrapUp,
  } = useConversation()

  const isSpeakingWhileMuted = useSpeechWhileMuted(activeStream, isMuted)

  const [showEndDialog, setShowEndDialog] = useState(false)
  const [showExtendDialog, setShowExtendDialog] = useState(false)
  const conversationStartRef = useRef(Date.now())
  const elapsedMsRef = useRef(0)

  // 롤플레이 시나리오에서 진입한 경우 navigation state로 topicId와 오프닝 대사가
  // 함께 전달된다 (없으면 conversationStore 기본값 'general_english' 그대로 자유대화로 진행).
  const routeState = location.state as
    | { topicId?: string; opening?: string | null; liveOpening?: string | null }
    | null
  const topicIdFromRoute = routeState?.topicId

  // 연습/실전 모드는 AI 튜터와 롤플레이에 동일하게 적용된다 — 모드 선택 화면에서
  // 고른 mode 그대로 사용.
  const mode = useConversationStore((s) => s.mode)
  const showTranscript = mode === 'practice'

  // 실전 모드에서는 "답변 완료"를 누르지 않아도, 말하다가 2.5초 침묵하면 전화
  // 통화처럼 자동으로 턴을 넘긴다. 연습 모드는 그대로 사용자가 명시적으로
  // 눌러야 끝나는 기존 방식을 유지한다.
  useAutoStopOnSilence(
    activeStream,
    !showTranscript && status === 'recording' && !isMuted,
    stopRecording
  )

  useEffect(() => {
    if (!userId) navigate('/', { replace: true })
  }, [userId, navigate])

  useEffect(() => {
    if (!isLoading && (!membership || !membership.plan.features.includes('conversation'))) {
      navigate('/', { replace: true })
    }
  }, [isLoading, membership, navigate])

  // AI speaks first after membership confirmed.
  // 마운트 직후 짧게(0ms) 지연시켜서 실행한다 — dev 모드에서 React.StrictMode나
  // 라우팅 전환 직후의 연속된 마운트/언마운트 잔여 효과가 가라앉을 시간을 준다.
  // 이게 없으면 막 시작된 인사말 TTS 요청이 그 직후의 정리(cleanup)에 취소되어
  // 인사말이 전혀 들리지 않는 문제가 있었다. 정리 함수에서 타이머를 취소하므로,
  // 실제로 살아남는 마운트에서만 한 번 실행된다.
  useEffect(() => {
    if (!isLoading && membership?.plan.features.includes('conversation')) {
      const timer = setTimeout(() => {
        reset()
        if (topicIdFromRoute) {
          setTopicId(topicIdFromRoute)
          setScenarioOpenings(routeState?.opening ?? null, routeState?.liveOpening ?? null)
        }
        startOpening()
      }, 0)
      return () => clearTimeout(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading])

  // 마이크 기본값 ON — AI가 말을 끝내고 idle로 돌아올 때마다(첫 인사 포함) 자동으로
  // 녹음을 다시 시작해, 매 턴마다 마이크 버튼을 직접 눌러야 하는 단계를 없앤다.
  // hasOpenedRef로 "최초 진입 시의 idle"(아직 AI가 인사하기 전)은 제외하고,
  // endedRef로 "전화 끊기 이후의 idle"에서는 다시 녹음을 시작하지 않도록 막는다.
  const hasOpenedRef = useRef(false)
  const endedRef = useRef(false)
  useEffect(() => {
    if (endedRef.current) return
    if (status !== 'idle') {
      hasOpenedRef.current = true
      return
    }
    if (hasOpenedRef.current) {
      // 방금 끝난 턴이 세션 30분 한도로 인한 "마무리 턴"이었으면, 다시 녹음을
      // 시작하는 대신 전화 끊기와 동일하게 강제 종료한다 (AI가 이미 작별 인사를 했음).
      if (wasLastTurnWrapUp()) {
        void handleEndCall()
        return
      }
      startRecording()
    }
  }, [status, startRecording])

  // 5/10/15/20/25분 지점마다 "연장하시겠습니까?" 다이얼로그를 띄운다. 통화가 이미
  // 끝났거나 다른 다이얼로그가 떠 있는 동안에는 묻지 않는다. 30분(세션 한도)에
  // 도달한 뒤에는 더 묻지 않는다 — 그 시점부터는 다음 AI 턴이 자연스럽게 마무리한다.
  useEffect(() => {
    const interval = setInterval(() => {
      if (endedRef.current || showEndDialog) return
      const sessionStartedAt = useConversationStore.getState().sessionStartedAt
      if (sessionStartedAt && Date.now() - sessionStartedAt >= SESSION_HARD_LIMIT_MS) return
      setShowExtendDialog(true)
    }, EXTEND_PROMPT_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [showEndDialog])

  const handleEndCall = async () => {
    endedRef.current = true
    elapsedMsRef.current = Date.now() - conversationStartRef.current
    await endCall()
    setShowEndDialog(true)
  }

  const handleEndFromExtendPrompt = () => {
    setShowExtendDialog(false)
    void handleEndCall()
  }

  // 30초 동안 연장/종료 중 아무것도 선택하지 않은 경우 — 자리를 비운 것으로 간주해
  // 종료 요약 화면 없이 곧바로 홈(내 멤버십 화면)으로 이동한다.
  const handleTimeoutFromExtendPrompt = async () => {
    setShowExtendDialog(false)
    endedRef.current = true
    await endCall()
    navigate('/')
  }

  if (!userId || isLoading) return null
  if (!membership?.plan.features.includes('conversation')) return null

  // vad_processing/stt_processing 동안에도 버튼을 계속 보여줘서 ∅(슬래시 마이크) 비활성 상태가
  // 눈에 보이게 한다 — 이전에는 버튼 자체가 사라져서 "꺼지는 느낌"이 전혀 안 보였다.
  const showRecorder =
    !showEndDialog &&
    !showExtendDialog &&
    (status === 'idle' ||
      status === 'recording' ||
      status === 'vad_processing' ||
      status === 'stt_processing')
  const showCancel = !showEndDialog && !showExtendDialog && CANCELLABLE.includes(status)
  const showError = status === 'error'
  const wordCount = messages
    .filter((m) => m.role === 'user')
    .reduce((sum, m) => sum + countWords(m.content), 0)

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* ── Header ── */}
      <header className="shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 max-w-2xl items-center gap-3">
          <Link to="/">
            <Button variant="ghost" size="sm" className="gap-1.5 text-muted-foreground">
              <ArrowLeft className="h-4 w-4" />
              홈
            </Button>
          </Link>
          <div className="flex flex-1 items-center gap-2 text-sm font-medium">
            <BookOpen className="h-4 w-4 text-primary" />
            AI 영어 튜터
            {!showTranscript && (
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                실전 모드
              </span>
            )}
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 rounded-full bg-gray-700 text-white hover:bg-gray-800 hover:text-white"
            onClick={() => void handleEndCall()}
            title="대화 종료"
          >
            <Phone className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* ── Message list (연습 모드) / 실전 모드 플레이스홀더 ── */}
      <div className="container flex min-h-0 flex-1 flex-col max-w-2xl">
        {showTranscript ? (
          <MessageList messages={messages} streamingContent={streamingContent} />
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 text-muted-foreground">
            <Phone className="h-10 w-10" />
            <p className="text-sm">AI 원어민과 통화 중입니다</p>
          </div>
        )}
      </div>

      {/* ── Bottom controls ── */}
      <div className="shrink-0 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container max-w-2xl space-y-3 py-4">
          {/* 마이크 on(recording, 음소거 아님)일 때만 파장(보라색 선)을 보여주고,
              음소거하면 즉시 사라진다. 음소거 중 소리가 감지되면 안내 문구로 대체한다. */}
          {status === 'recording' && !isMuted && <Waveform stream={activeStream} className="h-16" />}
          {status === 'recording' && isMuted && isSpeakingWhileMuted && (
            <p className="text-center text-sm font-medium text-amber-600">
              음소거 중입니다. 마이크를 켜주세요.
            </p>
          )}

          {/* Status label */}
          <ChatStatusBar status={status} error={error} isMuted={isMuted} />

          {/* ── Recorder controls ── */}
          {showRecorder && (
            <div className="flex justify-center">
              <AudioRecorder
                status={status}
                isMuted={isMuted}
                onStartRecording={startRecording}
                onToggleMute={toggleMute}
                onSubmit={stopRecording}
              />
            </div>
          )}

          {/* ── Cancel button: visible during any busy state ── */}
          {showCancel && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                className="gap-2 text-muted-foreground"
                onClick={cancel}
              >
                <X className="h-4 w-4" />
                취소
              </Button>
            </div>
          )}

          {/* ── Error state: retry + dismiss ── */}
          {showError && (
            <Alert variant="destructive">
              <AlertDescription>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm">{error ?? '오류가 발생했습니다.'}</span>
                  <div className="flex shrink-0 gap-2">
                    {canRetry && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1.5 border-destructive/40 text-destructive hover:bg-destructive/10"
                        onClick={() => void retry()}
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                        다시 시도
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive hover:bg-destructive/10"
                      onClick={dismissError}
                    >
                      닫기
                    </Button>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>

      <ExtendConversationDialog
        open={showExtendDialog}
        onExtend={() => setShowExtendDialog(false)}
        onEnd={handleEndFromExtendPrompt}
        onTimeout={() => void handleTimeoutFromExtendPrompt()}
      />

      <EndConversationDialog
        open={showEndDialog}
        onConfirm={() => navigate('/')}
        wordCount={wordCount}
        durationLabel={formatDuration(elapsedMsRef.current)}
        messages={messages}
      />
    </div>
  )
}
