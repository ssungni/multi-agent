import { useQuery } from '@tanstack/react-query'
import { membershipApi } from '@/services/membershipApi'
import { ApiError } from '@/services/apiClient'
import { useUserStore } from '@/stores/userStore'

// 현재 로그인한 사용자의 활성 멤버십 정보를 조회하는 쿼리 훅
export function useMembershipQuery() {
  const userId = useUserStore((s) => s.userId)

  return useQuery({
    queryKey: ['membership', userId],
    queryFn: async () => {
      try {
        const data = await membershipApi.getMyMembership()
        return data.membership
      } catch (err) {
        // 404 = 활성 멤버십 없음 — 정상 케이스, null 반환
        if (err instanceof ApiError && err.status === 404) return null
        throw err
      }
    },
    enabled: userId !== null,
  })
}
