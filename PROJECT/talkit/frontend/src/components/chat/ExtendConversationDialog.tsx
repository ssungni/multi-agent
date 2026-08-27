import { useEffect } from 'react'
import { Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

// 사용자가 응답하지 않고 방치할 수 있는 최대 대기 시간
const RESPONSE_TIMEOUT_MS = 30 * 1000

interface ExtendConversationDialogProps {
  open: boolean
  onExtend: () => void
  onEnd: () => void
  // 30초 안에 연장/종료 중 아무것도 선택하지 않으면 호출된다 — 자리를 비운 것으로
  // 간주해 종료 요약 화면 없이 곧바로 홈으로 보낸다 (onEnd와는 다른 동작).
  onTimeout: () => void
}

// 일정 시간(5분) 경과 후 대화를 연장할지 종료할지 묻는 다이얼로그 — 무응답 시 자동 타임아웃 처리
export function ExtendConversationDialog({
  open,
  onExtend,
  onEnd,
  onTimeout,
}: ExtendConversationDialogProps) {
  // 다이얼로그가 열려 있는 동안에만 타임아웃 타이머를 가동하고, 닫히면 타이머를 정리한다
  useEffect(() => {
    if (!open) return
    const timer = setTimeout(onTimeout, RESPONSE_TIMEOUT_MS)
    return () => clearTimeout(timer)
  }, [open, onTimeout])

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onExtend()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader className="items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-green-100">
            <Clock className="h-8 w-8 text-green-600" />
          </div>
          <DialogTitle className="text-xl">대화를 연장하시겠습니까?</DialogTitle>
        </DialogHeader>

        <p className="text-center text-sm text-muted-foreground">
          대화를 시작한 지 5분이 지났어요. (최대 30분까지 연장할 수 있어요)
        </p>

        <div className="grid grid-cols-2 gap-3">
          <Button variant="outline" onClick={onEnd}>
            종료하기
          </Button>
          <Button onClick={onExtend}>연장하기</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
