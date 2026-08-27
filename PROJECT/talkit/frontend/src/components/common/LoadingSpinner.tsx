// 로딩 상태를 표시하는 스피너 컴포넌트
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LoadingSpinnerProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

// size prop을 실제 너비/높이 클래스로 매핑하기 위한 테이블
const sizeMap = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
} as const

export function LoadingSpinner({ className, size = 'md', label }: LoadingSpinnerProps) {
  return (
    <div className={cn('flex items-center gap-2 text-muted-foreground', className)}>
      <Loader2 className={cn('animate-spin', sizeMap[size])} />
      {/* label이 있을 때만 보조 텍스트를 표시 */}
      {label && <span className="text-sm">{label}</span>}
    </div>
  )
}
