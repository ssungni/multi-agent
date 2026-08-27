import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useTopicsQuery } from './useTopicsQuery'
import { withQueryClient } from '@/test/test-utils'
import type { Topic } from '@/types/topic'

const { getTopicsMock } = vi.hoisted(() => ({ getTopicsMock: vi.fn() }))

vi.mock('@/services/topicApi', () => ({
  topicApi: { getTopics: getTopicsMock },
}))

const topics: Topic[] = [
  {
    id: 1,
    title: 'South Korea Keeps World Cup Hopes Alive',
    category: '월드컵',
    image_url: '/images/topics/01_wordcup.jpeg',
    english_1: 'English paragraph 1',
    korean_1: '한국어 문단 1',
    english_2: 'English paragraph 2',
    korean_2: '한국어 문단 2',
  },
]

describe('useTopicsQuery', () => {
  beforeEach(() => {
    getTopicsMock.mockReset()
  })

  it('topics 배열을 반환한다', async () => {
    getTopicsMock.mockResolvedValue({ topics })

    const { result } = renderHook(() => useTopicsQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(topics)
  })

  it('API 에러는 그대로 전파된다', async () => {
    getTopicsMock.mockRejectedValue(new Error('network error'))

    const { result } = renderHook(() => useTopicsQuery(), { wrapper: withQueryClient() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
