import { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { cn, formatCurrency } from '@/lib/utils'
import { extractErrorMessage } from '@/lib/networkError'
import { usePlansQuery } from '@/hooks/queries/usePlansQuery'
import { useGrantMembershipMutation } from '@/hooks/queries/useGrantMembershipMutation'
import type { AdminUser } from '@/types/admin'

interface GrantMembershipModalProps {
  user: AdminUser | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function GrantMembershipModal({ user, open, onOpenChange }: GrantMembershipModalProps) {
  const { data: plans, isLoading: plansLoading } = usePlansQuery()
  const [planId, setPlanId] = useState<number | null>(null)
  const { mutate, isPending, isError, error, reset } = useGrantMembershipMutation()

  // 모달이 다시 열릴 때마다 이전 선택/에러 상태를 초기화한다.
  useEffect(() => {
    if (open) {
      setPlanId(null)
      reset()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  if (!user) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!planId) return

    mutate(
      { user_id: user.id, membership_plan_id: planId },
      { onSuccess: () => onOpenChange(false) }
    )
  }

  const errorMessage = extractErrorMessage(
    error,
    (e) => `부여 실패: ${e.body.error}`,
    '멤버십 부여 중 오류가 발생했습니다.'
  )

  return (
    <Dialog open={open} onOpenChange={(next) => !isPending && onOpenChange(next)}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{user.name}님에게 멤버십 부여</DialogTitle>
          <DialogDescription>
            {user.active_membership
              ? `기존 ${user.active_membership.plan_name} 멤버십은 자동으로 교체(soft delete)됩니다.`
              : '부여할 플랜을 선택해주세요.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            {plansLoading && (
              <p className="text-sm text-muted-foreground">플랜 목록을 불러오는 중...</p>
            )}
            {plans?.map((plan) => (
              <button
                type="button"
                key={plan.id}
                onClick={() => setPlanId(plan.id)}
                className={cn(
                  'w-full rounded-md border p-3 text-left text-sm transition-colors',
                  planId === plan.id ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
                )}
              >
                <div className="font-medium">{plan.name}</div>
                <div className="text-muted-foreground">
                  {formatCurrency(plan.price_cents, plan.currency)} · {plan.duration_days}일
                </div>
              </button>
            ))}
          </div>

          {isError && (
            <Alert variant="destructive">
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          )}

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={isPending}
              onClick={() => onOpenChange(false)}
            >
              취소
            </Button>
            <Button type="submit" disabled={!planId || isPending}>
              {isPending ? '부여 중...' : '부여하기'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
