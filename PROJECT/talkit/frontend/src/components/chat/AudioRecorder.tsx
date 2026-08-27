import { Mic, MicOff, SendHorizonal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { ConversationStatus } from '@/types/conversation'

interface AudioRecorderProps {
  status: ConversationStatus
  isMuted: boolean
  onStartRecording: () => void
  onToggleMute: () => void
  onSubmit: () => void
}

// 녹음 시작/음소거 토글/답변 전송을 담당하는 마이크 버튼 UI
export function AudioRecorder({
  status,
  isMuted,
  onStartRecording,
  onToggleMute,
  onSubmit,
}: AudioRecorderProps) {
  const isRecording = status === 'recording'
  // 녹음/음소거 외의 처리 중(예: 인식, 응답 생성 등) 상태에서는 버튼을 비활성화한다
  const isBusy = status !== 'idle' && status !== 'recording' && status !== 'error'
  // 듣고 있는 중(녹음 중 + 음소거 아님)일 때만 "활성" 모습 — 그 외(아직 시작 전, 또는
  // 음소거)에는 모두 같은 "꺼짐" 모습으로 통일한다.
  const isActive = isRecording && !isMuted

  return (
    <div className="flex items-center gap-4">
      {/*
        듣고 있을 때(기본값) = 보라색 + 살아있는 펄스 + 일반 마이크(O) 아이콘
        음소거했을 때         = 옅은 보라색 + 애니메이션 정지(멈춘 느낌) + 슬래시 마이크(∅) 아이콘
        마이크 버튼은 더 이상 "답변 전송"을 의미하지 않는다 — 음소거 토글만 한다.
      */}
      <Button
        variant="ghost"
        size="lg"
        className={cn(
          'h-16 w-16 rounded-full p-0 text-white transition-all duration-300 ease-out',
          isActive
            ? 'scale-110 bg-green-600 shadow-lg shadow-green-500/40 ring-[6px] ring-green-400/40 hover:bg-green-600'
            : 'scale-100 bg-green-300 hover:bg-green-300',
          isBusy && 'opacity-50'
        )}
        disabled={isBusy}
        onClick={isRecording ? onToggleMute : onStartRecording}
        title={isRecording ? (isMuted ? '마이크 켜기' : '음소거') : '녹음 시작'}
      >
        {isActive ? (
          <Mic className="h-7 w-7 animate-pulse" />
        ) : (
          <MicOff className="h-7 w-7" />
        )}
      </Button>

      {/* 답변 완료 — 음소거 중이 아닐 때만 노출(음소거 중엔 보낼 새 발화가 없음) */}
      {isRecording && !isMuted && (
        <Button variant="outline" className="h-10 gap-2 px-4" onClick={onSubmit}>
          <SendHorizonal className="h-4 w-4" />
          답변 완료
        </Button>
      )}
    </div>
  )
}
