import { useMutation } from '@tanstack/react-query'
import { userApi } from '@/services/userApi'

// 로그인을 요청하는 뮤테이션 훅
export function useLoginMutation() {
  return useMutation({
    mutationFn: userApi.login,
  })
}
