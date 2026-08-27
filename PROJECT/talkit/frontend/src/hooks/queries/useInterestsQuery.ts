import { useQuery } from '@tanstack/react-query'
import { interestsApi } from '@/services/interestsApi'
import { useUserStore } from '@/stores/userStore'

// 현재 로그인한 사용자의 관심사 목록을 조회하는 쿼리 훅
export function useInterestsQuery() {
  const userId = useUserStore((s) => s.userId)

  return useQuery({
    queryKey: ['interests', userId],
    queryFn: async () => (await interestsApi.getInterests()).interests,
    enabled: userId !== null,
  })
}
