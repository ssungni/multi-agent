import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/services/adminApi'
import { useUserStore } from '@/stores/userStore'

// 어드민용 사용자 목록을 페이지 단위로 조회하는 쿼리 훅
export function useAdminUsersQuery(page = 1) {
  const adminToken = useUserStore((s) => s.adminToken)

  return useQuery({
    queryKey: ['admin', 'users', page],
    queryFn: () => adminApi.getUsers(page),
    enabled: !!adminToken, // 어드민 토큰이 없으면 요청 자체를 막음
    retry: false, // 토큰 인증 실패 시 자동 재시도하지 않음
  })
}
