import { Link } from 'react-router-dom'
import { CalendarDays, Clock, MessageCircle, Users, BookOpen, Sparkles } from 'lucide-react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDate } from '@/lib/utils'
import { FEATURE_LABELS, LOW_DAYS_THRESHOLD } from '@/lib/constants'
import type { UserMembership } from '@/types/membership'

interface ActiveMembershipCardProps {
  membership: UserMembership | null
  isLoading: boolean
}

export function ActiveMembershipCard({ membership, isLoading }: ActiveMembershipCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-40" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-16 rounded-full" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!membership) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="text-base text-muted-foreground">활성 멤버십 없음</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            아래 플랜을 선택하여 AI 튜터링을 시작해보세요.
          </p>
        </CardContent>
      </Card>
    )
  }

  const hasLearning = membership.plan.features.includes('learning')
  const hasConversation = membership.plan.features.includes('conversation')
  const isExpiringSoon = membership.days_remaining <= LOW_DAYS_THRESHOLD

  return (
    <Card className="border-green-200 bg-green-50/50">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-green-600" />
              <CardTitle className="text-lg">{membership.plan.name}</CardTitle>
            </div>
            <Badge variant="success">활성</Badge>
          </div>
          <Badge variant={isExpiringSoon ? 'warning' : 'secondary'}>
            {membership.days_remaining}일 남음
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 기능 배지 */}
        <div className="flex flex-wrap gap-2">
          {membership.plan.features.map((feature) => (
            <Badge key={feature} variant="outline" className="text-xs">
              {FEATURE_LABELS[feature] ?? feature}
            </Badge>
          ))}
        </div>

        {/* 날짜 정보 */}
        <div className="space-y-1.5 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-3.5 w-3.5 shrink-0" />
            <span>시작: {formatDate(membership.starts_at)}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-3.5 w-3.5 shrink-0" />
            <span className={isExpiringSoon ? 'font-medium text-amber-600' : ''}>
              만료: {formatDate(membership.expires_at)}
              {isExpiringSoon && ' (곧 만료)'}
            </span>
          </div>
        </div>
      </CardContent>

      {/* 기능 진입 버튼 — AI 튜터 → AI 롤플레이 → 토픽 순 (보유 기능에 따라 표시) */}
      {(hasConversation || hasLearning) && (
        <CardFooter className="flex flex-col gap-2">
          {hasConversation && (
            <Button asChild className="w-full">
              <Link to="/tutor">
                <MessageCircle className="mr-2 h-4 w-4" />
                AI 튜터
              </Link>
            </Button>
          )}
          {hasConversation && (
            <Button asChild variant="outline" className="w-full">
              <Link to="/roleplay">
                <Users className="mr-2 h-4 w-4" />
                AI 롤플레이
              </Link>
            </Button>
          )}
          {hasLearning && (
            <Button asChild variant="outline" className="w-full">
              <Link to="/topics">
                <BookOpen className="mr-2 h-4 w-4" />
                토픽
              </Link>
            </Button>
          )}
        </CardFooter>
      )}
    </Card>
  )
}
