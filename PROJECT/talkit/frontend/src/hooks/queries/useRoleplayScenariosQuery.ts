import { useQuery } from '@tanstack/react-query'
import { roleplayApi } from '@/services/roleplayApi'

// 롤플레이 시나리오 목록을 조회하는 쿼리 훅
export function useRoleplayScenariosQuery() {
  return useQuery({
    queryKey: ['roleplay-scenarios'],
    queryFn: async () => (await roleplayApi.getScenarios()).roleplay_scenarios,
    staleTime: 1000 * 60 * 5, // 시나리오 목록은 자주 바뀌지 않으므로 5분간 재요청하지 않음
  })
}
