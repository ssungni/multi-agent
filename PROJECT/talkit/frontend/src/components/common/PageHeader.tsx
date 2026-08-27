import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'

interface PageHeaderProps {
  icon: LucideIcon
  title: ReactNode
  actions?: ReactNode
}

// "홈으로" 버튼 + 아이콘 + 타이틀로 구성된 상단 헤더 — 뒤로가기가 있는 하위 페이지들
// (토픽/롤플레이/모드 선택/프로필/어드민 등)에서 반복되던 마크업을 통합한다.
// HomePage(뒤로가기가 없음)와 ChatPage(sticky가 아닌 다른 레이아웃 구조)는 이 컴포넌트를 쓰지 않는다.
export function PageHeader({ icon: Icon, title, actions }: PageHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
      <div className="container flex h-14 max-w-2xl items-center gap-3">
        <Link to="/">
          <Button variant="ghost" size="sm" className="gap-1.5 text-muted-foreground">
            <ArrowLeft className="h-4 w-4" />
            홈
          </Button>
        </Link>
        <div className="flex flex-1 items-center gap-2 text-sm font-medium">
          <Icon className="h-4 w-4 text-primary" />
          {title}
        </div>
        {actions}
      </div>
    </header>
  )
}
