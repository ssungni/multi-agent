import { useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/services/adminApi'

// 어드민이 특정 사용자에게 멤버십을 부여하는 뮤테이션 훅
export function useGrantMembershipMutation() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: adminApi.grantMembership,
    onSuccess: () => {
      // 멤버십 부여 결과를 목록에 즉시 반영하기 위해 사용자 목록 쿼리 무효화
      qc.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
  })
}
