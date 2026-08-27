// 앱 전역에서 사용하는 React Query 클라이언트 — 캐시 정책과 재시도 정책을 한 곳에서 관리한다.
import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '@/services/apiClient'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,
      // ApiError 상태코드에 따라 재시도 여부를 다르게 판단한다.
      retry: (count, err) => {
        if (err instanceof ApiError) {
          // 인증/권한/리소스 없음 — 재시도 불필요
          if ([401, 403, 404].includes(err.status)) return false
        }
        return count < 2
      },
    },
  },
})
