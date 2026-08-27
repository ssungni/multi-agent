import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { PlanCard } from '@/components/membership/PlanCard'
import type { MembershipPlan, UserMembership } from '@/types/membership'

interface PlanListProps {
  plans: MembershipPlan[] | undefined
  isLoading: boolean
  currentMembership: UserMembership | null
  onSelectPlan: (plan: MembershipPlan) => void
}

function PlanCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-8 w-32" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
        </div>
        <Skeleton className="h-10 w-full" />
      </CardContent>
    </Card>
  )
}

export function PlanList({ plans, isLoading, currentMembership, onSelectPlan }: PlanListProps) {
  if (isLoading) {
    return (
      <div className="flex gap-4 overflow-x-auto pb-2">
        <div className="w-72 shrink-0">
          <PlanCardSkeleton />
        </div>
        <div className="w-72 shrink-0">
          <PlanCardSkeleton />
        </div>
      </div>
    )
  }

  if (!plans || plans.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        현재 이용 가능한 플랜이 없습니다.
      </p>
    )
  }

  // 가격이 높은(보통 더 많은 기능을 포함하는) 플랜을 왼쪽에 먼저 보여준다.
  const sortedPlans = [...plans].sort((a, b) => b.price_cents - a.price_cents)

  return (
    <div className="flex snap-x snap-mandatory gap-4 overflow-x-auto pb-2">
      {sortedPlans.map((plan) => (
        <div key={plan.id} className="w-72 shrink-0 snap-start">
          <PlanCard
            plan={plan}
            isCurrentPlan={currentMembership?.plan.id === plan.id}
            onSelect={onSelectPlan}
          />
        </div>
      ))}
    </div>
  )
}
