// 네트워크 오프라인 상태를 감지해 화면 상단에 경고 배너를 표시하는 컴포넌트
import { WifiOff } from 'lucide-react'
import { useOnlineStatus } from '@/hooks/useOnlineStatus'

export function OfflineBanner() {
  const isOnline = useOnlineStatus()
  // 온라인 상태에서는 배너를 표시할 필요가 없으므로 아무것도 렌더링하지 않음
  if (isOnline) return null

  return (
    <div
      role="alert"
      className="fixed inset-x-0 top-0 z-50 flex items-center justify-center gap-2 bg-destructive py-2 text-sm font-medium text-destructive-foreground"
    >
      <WifiOff className="h-4 w-4" />
      네트워크 연결 오류 — 인터넷 연결을 확인해주세요.
    </div>
  )
}
