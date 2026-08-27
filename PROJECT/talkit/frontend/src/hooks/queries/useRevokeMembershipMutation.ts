import { useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/services/adminApi'

// 어드민이 특정 사용자의 멤버십을 회수하는 뮤테이션 훅
export function useRevokeMembershipMutation() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (membershipId: number) => adminApi.revokeMembership(membershipId),
    onSuccess: () => {
      // 멤버십 회수 결과를 목록에 즉시 반영하기 위해 사용자 목록 쿼리 무효화
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
  })
}
