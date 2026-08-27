import { useMutation, useQueryClient } from '@tanstack/react-query'
import { paymentApi } from '@/services/paymentApi'
import { useUserStore } from '@/stores/userStore'
import type { PaymentRequest } from '@/types/payment'

// 결제를 요청하는 뮤테이션 훅
export function usePaymentMutation() {
  const qc = useQueryClient()
  const userId = useUserStore((s) => s.userId)

  return useMutation({
    mutationFn: (body: PaymentRequest) => paymentApi.create(body),
    onSuccess: () => {
      // 결제 성공 → 멤버십 즉시 갱신
      qc.invalidateQueries({ queryKey: ['membership', userId] })
    },
  })
}
