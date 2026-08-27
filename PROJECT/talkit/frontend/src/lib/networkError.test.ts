import { describe, it, expect } from 'vitest'
import { isNetworkError } from './networkError'
import { ApiError } from '@/services/apiClient'

describe('isNetworkError', () => {
  it('TypeError(fetch 네트워크 실패)는 true를 반환한다', () => {
    expect(isNetworkError(new TypeError('Failed to fetch'))).toBe(true)
  })

  it('일반 Error는 false를 반환한다', () => {
    expect(isNetworkError(new Error('something else'))).toBe(false)
  })

  it('ApiError(정상 HTTP 에러 응답)는 false를 반환한다', () => {
    expect(isNetworkError(new ApiError(500, { error: 'server_error' }))).toBe(false)
  })

  it('Error가 아닌 값(string, null, undefined)은 false를 반환한다', () => {
    expect(isNetworkError('boom')).toBe(false)
    expect(isNetworkError(null)).toBe(false)
    expect(isNetworkError(undefined)).toBe(false)
  })
})
