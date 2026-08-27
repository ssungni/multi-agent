import { useQuery } from '@tanstack/react-query'
import { topicApi } from '@/services/topicApi'

// 학습용 토픽 목록을 조회하는 쿼리 훅
export function useTopicsQuery() {
  return useQuery({
    queryKey: ['topics'],
    queryFn: async () => (await topicApi.getTopics()).topics,
    staleTime: 1000 * 60 * 5, // 토픽 목록은 자주 바뀌지 않으므로 5분간 재요청하지 않음
  })
}
