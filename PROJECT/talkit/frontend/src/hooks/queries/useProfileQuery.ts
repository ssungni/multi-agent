import { useQuery } from '@tanstack/react-query'
import { profileApi } from '@/services/profileApi'
import { useUserStore } from '@/stores/userStore'

// 현재 로그인한 사용자의 프로필 정보를 조회하는 쿼리 훅
export function useProfileQuery() {
  const userId = useUserStore((s) => s.userId)

  return useQuery({
    queryKey: ['profile', userId],
    queryFn: () => profileApi.getProfile(),
    enabled: userId !== null,
  })
}
