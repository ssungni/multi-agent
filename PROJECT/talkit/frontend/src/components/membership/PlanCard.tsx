import { Check } from 'lucide-react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatCurrency } from '@/lib/utils'
import type { MembershipFeature, MembershipPlan } from '@/types/membership'

interface PlanCardProps {
  plan: MembershipPlan
  isCurrentPlan?: boolean
  onSelect: (plan: MembershipPlan) => void
}

// 플랜 비교 카드에 표시할 항목 — "AI 롤플레잉"과 "AI 디스커션"은 둘 다
// conversation 기능 하나에 묶여있는 마케팅용 세부 항목이라 별도 feature 컬럼은 아니다.
const PLAN_FEATURE_ITEMS: Array<{ key: MembershipFeature; label: string }> = [
  { key: 'learning', label: 'AI 표현 학습' },
  { key: 'conversation', label: 'AI 롤플레잉' },
  { key: 'conversation', label: 'AI 디스커션' },
  { key: 'analysis', label: '무제한 AI 분석' },
]

export function PlanCard({ plan, isCurrentPlan = false, onSelect }: PlanCardProps) {
  const isPremium = plan.features.includes('conversation')

  return (
    <Card className={isPremium ? 'border-primary shadow-md' : ''}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{plan.name}</CardTitle>
          {isPremium && (
            <Badge className="text-xs">추천</Badge>
          )}
        </div>
        <CardDescription>
          <span className="text-2xl font-bold text-foreground">
            {formatCurrency(plan.price_cents, plan.currency)}
          </span>
          <span className="ml-1 text-sm">/ {plan.duration_days}일</span>
        </CardDescription>
      </CardHeader>

      <CardContent>
        <ul className="space-y-2">
          {PLAN_FEATURE_ITEMS.map(({ key, label }) => {
            const included = plan.features.includes(key)
            return (
              <li
                key={label}
                className={`flex items-center gap-2 text-sm ${
                  included ? 'text-foreground' : 'text-muted-foreground line-through'
                }`}
              >
                <Check
                  className={`h-4 w-4 shrink-0 ${
                    included ? 'text-green-500' : 'text-muted-foreground/40'
                  }`}
                />
                {label}
              </li>
            )
          })}
        </ul>
      </CardContent>

      <CardFooter>
        <Button
          className="w-full"
          variant={isPremium ? 'default' : 'outline'}
          onClick={() => onSelect(plan)}
          disabled={isCurrentPlan}
        >
          {isCurrentPlan ? '현재 플랜' : '구매'}
        </Button>
      </CardFooter>
    </Card>
  )
}
