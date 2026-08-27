import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ConversationStatus } from '@/types/conversation'

// 대화 진행 상태(ConversationStatus)별로 사용자에게 보여줄 안내 문구
const STATUS_LABELS: Record<ConversationStatus, string> = {
  idle: '마이크 버튼을 눌러 대화를 시작하세요',
  ai_opening: 'AI 인사말 재생 중...',
  recording: '녹음 중 — 답변 완료 버튼을 눌러 전송',
  vad_processing: '음성 감지 중...',
  stt_processing: '음성 인식 중...',
  llm_streaming: 'AI 응답 생성 중...',
  tts_playing: '음성 재생 중...',
  error: '오류 발생',
}

// 처리 중임을 나타내기 위해 스피너를 보여줘야 하는 상태 목록
const SPINNING: ConversationStatus[] = [
  'ai_opening',
  'vad_processing',
  'stt_processing',
  'llm_streaming',
  'tts_playing',
]

interface ChatStatusBarProps {
  status: ConversationStatus
  error: string | null
  isMuted?: boolean
}

// 현재 대화 상태를 텍스트와 스피너로 보여주는 상태 표시줄
export function ChatStatusBar({ status, error, isMuted = false }: ChatStatusBarProps) {
  const spinning = SPINNING.includes(status)
  const isError = status === 'error'
  // 우선순위: 에러 메시지 > 녹음 중 음소거 안내 > 기본 상태 라벨
  const label = isError
    ? error ?? '알 수 없는 오류'
    : status === 'recording' && isMuted
      ? '음소거 중 — 마이크를 눌러 다시 켜세요'
      : STATUS_LABELS[status]

  return (
    <div className="flex items-center justify-center gap-2 text-sm">
      {spinning && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}
      <span className={cn('text-muted-foreground', isError && 'text-destructive')}>{label}</span>
    </div>
  )
}
