import { useMutation, useQueryClient } from '@tanstack/react-query'
import { interestsApi } from '@/services/interestsApi'
import { useUserStore } from '@/stores/userStore'

// 사용자의 관심사 목록을 수정하는 뮤테이션 훅
export function useUpdateInterestsMutation() {
  const qc = useQueryClient()
  const userId = useUserStore((s) => s.userId)

  return useMutation({
    mutationFn: (interests: string[]) => interestsApi.updateInterests(interests),
    onSuccess: (data) => {
      // 재요청 없이 응답값으로 캐시를 직접 갱신해 즉시 최신 상태 반영
      qc.setQueryData(['interests', userId], data.interests)
    },
  })
}
