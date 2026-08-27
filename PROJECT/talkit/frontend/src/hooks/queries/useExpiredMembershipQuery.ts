import { useQuery } from '@tanstack/react-query'
import { membershipApi } from '@/services/membershipApi'
import { ApiError } from '@/services/apiClient'
import { useUserStore } from '@/stores/userStore'
import type { UserMembership } from '@/types/membership'

// 활성 멤버십이 없을 때, "한 번도 결제 안 함"과 "만료됨"을 구분해서 보여주기 위한 훅.
// GET /me/membership이 404일 때 함께 내려주는 expired_membership을 읽는다.
// (활성 멤버십이 있으면 애초에 보여줄 필요가 없으므로 null을 반환한다.)
export function useExpiredMembershipQuery() {
  const userId = useUserStore((s) => s.userId)

  return useQuery({
    queryKey: ['expired-membership', userId],
    queryFn: async (): Promise<UserMembership | null> => {
      try {
        await membershipApi.getMyMembership()
        return null
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return err.body.expired_membership ?? null
        }
        throw err
      }
    },
    enabled: userId !== null,
  })
}
