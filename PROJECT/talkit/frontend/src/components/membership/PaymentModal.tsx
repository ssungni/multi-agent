import { useState } from 'react'
import { AlertCircle, CreditCard, Info } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { formatCurrency } from '@/lib/utils'
import { MOCK_CARD_TOKENS } from '@/lib/constants'
import { extractErrorMessage } from '@/lib/networkError'
import { usePaymentMutation } from '@/hooks/queries/usePaymentMutation'
import type { MembershipPlan } from '@/types/membership'

interface PaymentModalProps {
  plan: MembershipPlan | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function PaymentModal({ plan, open, onOpenChange }: PaymentModalProps) {
  const [cardToken, setCardToken] = useState(MOCK_CARD_TOKENS.success)
  const [confirming, setConfirming] = useState(false)
  const { mutate, isPending, isError, error, reset } = usePaymentMutation()

  const handleOpenChange = (nextOpen: boolean) => {
    if (isPending) return
    if (!nextOpen) {
      reset()
      setConfirming(false)
    }
    onOpenChange(nextOpen)
  }

  // "결제하기" 클릭 시 바로 결제하지 않고, 먼저 "결제하시겠습니까?" 확인 단계를 보여준다.
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!plan) return
    setConfirming(true)
  }

  const handleConfirmPayment = () => {
    if (!plan) return

    mutate(
      {
        membership_plan_id: plan.id,
        payment_method: 'card',
        card_token: cardToken.trim(),
      },
      {
        onSuccess: () => {
          handleOpenChange(false)
        },
        onError: () => {
          setConfirming(false)
        },
      }
    )
  }

  const errorMessage = extractErrorMessage(
    error,
    (e) => `결제 실패: ${e.body.error}`,
    '결제 중 오류가 발생했습니다. 다시 시도해주세요.'
  )

  if (!plan) return null

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            {plan.name} 결제
          </DialogTitle>
          <DialogDescription>
            결제 후 즉시 멤버십이 활성화됩니다.
          </DialogDescription>
        </DialogHeader>

        {confirming ? (
          <>
            <div className="rounded-lg border bg-muted/40 p-4 space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">플랜</span>
                <span className="font-medium">{plan.name}</span>
              </div>
              <Separator />
              <div className="flex justify-between font-semibold">
                <span>결제 금액</span>
                <span>{formatCurrency(plan.price_cents, plan.currency)}</span>
              </div>
            </div>

            <p className="mb-4 text-center text-sm font-medium">결제하시겠습니까?</p>

            {isError && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
            )}

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setConfirming(false)}
                disabled={isPending}
              >
                취소
              </Button>
              <Button type="button" onClick={handleConfirmPayment} disabled={isPending}>
                {isPending ? '결제 처리 중...' : '네, 결제할게요'}
              </Button>
            </DialogFooter>
          </>
        ) : (
        <form onSubmit={handleSubmit}>
          {/* 플랜 요약 */}
          <div className="rounded-lg border bg-muted/40 p-4 space-y-2 mb-4">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">플랜</span>
              <span className="font-medium">{plan.name}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">이용 기간</span>
              <span className="font-medium">{plan.duration_days}일</span>
            </div>
            <Separator />
            <div className="flex justify-between font-semibold">
              <span>결제 금액</span>
              <span>{formatCurrency(plan.price_cents, plan.currency)}</span>
            </div>
          </div>

          {/* 카드 토큰 입력 */}
          <div className="space-y-2 mb-4">
            <Label htmlFor="card-token">카드 토큰 (Mock)</Label>
            <Input
              id="card-token"
              value={cardToken}
              onChange={(e) => {
                setCardToken(e.target.value)
                if (isError) reset()
              }}
              placeholder={MOCK_CARD_TOKENS.success}
              disabled={isPending}
              autoComplete="off"
            />

            {/* 테스트 토큰 안내 */}
            <div className="rounded-md border border-blue-200 bg-blue-50 p-3">
              <div className="flex items-start gap-2">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-blue-500" />
                <div className="text-xs text-blue-700 space-y-1">
                  <p className="font-medium">테스트 카드 토큰</p>
                  <p>
                    성공:{' '}
                    <code className="rounded bg-blue-100 px-1">{MOCK_CARD_TOKENS.success}</code>
                  </p>
                  <p>
                    잔액부족:{' '}
                    <code className="rounded bg-blue-100 px-1">{MOCK_CARD_TOKENS.fail}</code>
                  </p>
                  <p>
                    만료카드:{' '}
                    <code className="rounded bg-blue-100 px-1">{MOCK_CARD_TOKENS.expired}</code>
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 에러 메시지 */}
          {isError && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          )}

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isPending}
            >
              취소
            </Button>
            <Button type="submit" disabled={isPending || !cardToken.trim()}>
              {isPending ? '결제 처리 중...' : `${formatCurrency(plan.price_cents, plan.currency)} 결제하기`}
            </Button>
          </DialogFooter>
        </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
