import { useMutation } from '@tanstack/react-query'
import { adminApi } from '@/services/adminApi'

// 어드민 토큰을 스토어에 커밋하기 전에 실제로 유효한지 먼저 확인한다.
// (틀린 토큰으로 바로 어드민 화면에 진입했다가 에러를 보여주는 대신, 토큰 입력 화면에서 막는다)
export function useVerifyAdminTokenMutation() {
  return useMutation({
    mutationFn: (token: string) => adminApi.getUsers(1, token),
  })
}
