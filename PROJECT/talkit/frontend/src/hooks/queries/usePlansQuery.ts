import { useQuery } from '@tanstack/react-query'
import { membershipApi } from '@/services/membershipApi'

// 멤버십 플랜 목록을 조회하는 쿼리 훅
export function usePlansQuery() {
  return useQuery({
    queryKey: ['plans'],
    queryFn: async () => {
      const data = await membershipApi.getPlans()
      return data.plans
    },
    staleTime: 1000 * 60 * 5, // 플랜 정보는 자주 바뀌지 않으므로 5분간 재요청하지 않음
  })
}
