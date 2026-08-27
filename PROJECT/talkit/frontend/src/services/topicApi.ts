// 학습 토픽 목록 조회를 담당하는 API 서비스
import { apiRequest } from '@/services/apiClient'
import type { Topic } from '@/types/topic'

export const topicApi = {
  // 전체 토픽 목록을 조회
  getTopics: () => apiRequest<{ topics: Topic[] }>('/topics'),
}
