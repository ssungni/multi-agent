import { useMutation } from '@tanstack/react-query'
import { userApi } from '@/services/userApi'

// 회원가입을 요청하는 뮤테이션 훅
export function useSignupMutation() {
  return useMutation({
    mutationFn: userApi.signup,
  })
}
