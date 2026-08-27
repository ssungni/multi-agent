// 에러 상황을 알리고 필요 시 재시도를 제공하는 배너 컴포넌트
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

interface ErrorBannerProps {
  message?: string
  onRetry?: () => void
}

export function ErrorBanner({
  message = '데이터를 불러오는 중 오류가 발생했습니다.',
  onRetry,
}: ErrorBannerProps) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>오류</AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span>{message}</span>
        {/* onRetry가 전달된 경우에만 재시도 버튼을 노출 */}
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry} className="ml-4 shrink-0">
            <RefreshCw className="mr-1 h-3 w-3" />
            재시도
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}
