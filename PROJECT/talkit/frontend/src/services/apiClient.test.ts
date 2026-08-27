import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiRequest, apiRequestForm, ApiError } from './apiClient'
import { useUserStore } from '@/stores/userStore'

describe('apiClient', () => {
  beforeEach(() => {
    useUserStore.setState({ userId: null, adminToken: null })
    vi.stubGlobal('fetch', vi.fn())
  })

  describe('apiRequest', () => {
    it('성공 응답의 JSON 바디를 반환한다', async () => {
      vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }))

      const result = await apiRequest<{ ok: boolean }>('/test')
      expect(result).toEqual({ ok: true })
    })

    it('API_BASE_URL을 경로 앞에 붙인다', async () => {
      vi.mocked(fetch).mockResolvedValue(new Response('{}', { status: 200 }))

      await apiRequest('/membership_plans')

      expect(fetch).toHaveBeenCalledWith('/api/v1/membership_plans', expect.any(Object))
    })

    it('userId가 설정되어 있으면 X-User-Id 헤더를 포함한다', async () => {
      useUserStore.setState({ userId: 7 })
      vi.mocked(fetch).mockResolvedValue(new Response('{}', { status: 200 }))

      await apiRequest('/test')

      const [, init] = vi.mocked(fetch).mock.calls[0]!
      expect((init!.headers as Record<string, string>)['X-User-Id']).toBe('7')
    })

    it('userId가 없으면 X-User-Id 헤더를 포함하지 않는다', async () => {
      vi.mocked(fetch).mockResolvedValue(new Response('{}', { status: 200 }))

      await apiRequest('/test')

      const [, init] = vi.mocked(fetch).mock.calls[0]!
      expect((init!.headers as Record<string, string>)['X-User-Id']).toBeUndefined()
    })

    it('admin 옵션이 true이면 X-Admin-Token만 포함하고 X-User-Id는 제외한다', async () => {
      useUserStore.setState({ userId: 7, adminToken: 'secret' })
      vi.mocked(fetch).mockResolvedValue(new Response('{}', { status: 200 }))

      await apiRequest('/admin/test', {}, { admin: true })

      const [, init] = vi.mocked(fetch).mock.calls[0]!
      const headers = init!.headers as Record<string, string>
      expect(headers['X-Admin-Token']).toBe('secret')
      expect(headers['X-User-Id']).toBeUndefined()
    })

    it('adminToken을 명시적으로 전달하면 스토어 값 대신 그것을 사용한다 (토큰 검증용)', async () => {
      useUserStore.setState({ adminToken: 'stored-token' })
      vi.mocked(fetch).mockResolvedValue(new Response('{}', { status: 200 }))

      await apiRequest('/admin/test', {}, { admin: true, adminToken: 'candidate-token' })

      const [, init] = vi.mocked(fetch).mock.calls[0]!
      const headers = init!.headers as Record<string, string>
      expect(headers['X-Admin-Token']).toBe('candidate-token')
    })

    it('실패 응답이면 ApiError(status, body)를 던진다', async () => {
      vi.mocked(fetch).mockResolvedValue(
        new Response(JSON.stringify({ error: 'not_found' }), { status: 404 })
      )

      await expect(apiRequest('/missing')).rejects.toMatchObject({
        status: 404,
        body: { error: 'not_found' },
      })
    })

    it('에러 응답 바디가 JSON이 아니면 unknown_error로 대체한다', async () => {
      vi.mocked(fetch).mockResolvedValue(new Response('not json', { status: 500 }))

      await expect(apiRequest('/broken')).rejects.toMatchObject({
        status: 500,
        body: { error: 'unknown_error' },
      })
    })
  })

  describe('apiRequestForm', () => {
    it('FormData를 POST으로 전송하고 Content-Type을 직접 설정하지 않는다', async () => {
      vi.mocked(fetch).mockResolvedValue(
        new Response(JSON.stringify({ text: 'hi' }), { status: 200 })
      )

      const formData = new FormData()
      formData.append('audio', new Blob(['x']), 'audio.webm')

      const result = await apiRequestForm<{ text: string }>('/conversations/stt', formData)

      expect(result).toEqual({ text: 'hi' })
      const [, init] = vi.mocked(fetch).mock.calls[0]!
      expect(init!.method).toBe('POST')
      expect(init!.body).toBe(formData)
      expect((init!.headers as Record<string, string>)['Content-Type']).toBeUndefined()
    })

    it('실패 응답이면 ApiError를 던진다', async () => {
      vi.mocked(fetch).mockResolvedValue(
        new Response(JSON.stringify({ error: 'invalid_audio' }), { status: 422 })
      )

      await expect(apiRequestForm('/conversations/stt', new FormData())).rejects.toMatchObject({
        status: 422,
      })
    })
  })

  describe('ApiError', () => {
    it('message에 상태코드와 error 코드를 포함하고 name이 ApiError이다', () => {
      const err = new ApiError(403, { error: 'feature_not_allowed' })
      expect(err.message).toBe('HTTP 403: feature_not_allowed')
      expect(err.name).toBe('ApiError')
      expect(err.status).toBe(403)
      expect(err.body).toEqual({ error: 'feature_not_allowed' })
    })
  })
})
