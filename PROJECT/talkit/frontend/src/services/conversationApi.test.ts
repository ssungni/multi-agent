import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { conversationApi } from './conversationApi'
import { useUserStore } from '@/stores/userStore'
import { ApiError } from '@/services/apiClient'

describe('conversationApi', () => {
  beforeEach(() => {
    useUserStore.setState({ userId: 5, adminToken: null })
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('stt', () => {
    it('성공 시 { text } 를 반환하고 FormData로 multipart 요청을 보낸다', async () => {
      vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ text: 'hello' }), { status: 200 }))

      const result = await conversationApi.stt(new Blob(['audio']))

      expect(result).toEqual({ text: 'hello' })
      const [url, init] = vi.mocked(fetch).mock.calls[0]!
      expect(url).toBe('/api/v1/conversations/stt')
      expect(init!.body).toBeInstanceOf(FormData)
      expect((init!.headers as Record<string, string>)['X-User-Id']).toBe('5')
    })

    it('audioBlob이 wav면 recording.wav로, 그 외에는 recording.webm으로 업로드한다', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ text: 'hi' }), { status: 200 }))
      await conversationApi.stt(new Blob(['wav-bytes'], { type: 'audio/wav' }))
      const [, init] = vi.mocked(fetch).mock.calls[0]!
      const file = (init!.body as FormData).get('audio') as File
      expect(file.name).toBe('recording.wav')

      vi.mocked(fetch).mockClear()
      vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ text: 'hi' }), { status: 200 }))
      await conversationApi.stt(new Blob(['webm-bytes'], { type: 'audio/webm;codecs=opus' }))
      const [, init2] = vi.mocked(fetch).mock.calls[0]!
      const file2 = (init2!.body as FormData).get('audio') as File
      expect(file2.name).toBe('recording.webm')
    })

    it('일시적 실패 후 재시도하여 성공한다', async () => {
      vi.useFakeTimers()
      vi.mocked(fetch)
        .mockResolvedValueOnce(new Response('{}', { status: 500 }))
        .mockResolvedValueOnce(new Response(JSON.stringify({ text: 'ok' }), { status: 200 }))

      const promise = conversationApi.stt(new Blob(['audio']))
      await vi.runAllTimersAsync()

      expect(await promise).toEqual({ text: 'ok' })
      expect(fetch).toHaveBeenCalledTimes(2)
    })

    it('401/403/429는 재시도하지 않고 즉시 ApiError를 던진다', async () => {
      vi.mocked(fetch).mockResolvedValue(
        new Response(JSON.stringify({ error: 'feature_not_allowed' }), { status: 403 })
      )

      await expect(conversationApi.stt(new Blob(['audio']))).rejects.toBeInstanceOf(ApiError)
      expect(fetch).toHaveBeenCalledTimes(1)
    })

    it('2번 재시도 후에도 실패하면 마지막 에러를 던진다', async () => {
      vi.useFakeTimers()
      vi.mocked(fetch).mockResolvedValue(new Response('{}', { status: 500 }))

      const promise = conversationApi.stt(new Blob(['audio']))
      const expectation = expect(promise).rejects.toBeInstanceOf(ApiError)
      await vi.runAllTimersAsync()
      await expectation

      expect(fetch).toHaveBeenCalledTimes(3) // 최초 1회 + 재시도 2회
    })
  })

  describe('tts', () => {
    it('성공 시 Blob을 반환하고 JSON body로 텍스트를 전달한다', async () => {
      const audioBlob = new Blob(['mp3-bytes'], { type: 'audio/mpeg' })
      vi.mocked(fetch).mockResolvedValue(new Response(audioBlob, { status: 200 }))

      const result = await conversationApi.tts('Hello world')

      expect(result).toBeInstanceOf(Blob)
      const [, init] = vi.mocked(fetch).mock.calls[0]!
      expect(init!.body).toBe(JSON.stringify({ text: 'Hello world' }))
      expect((init!.headers as Record<string, string>)['Content-Type']).toBe('application/json')
    })
  })

  describe('chatStream', () => {
    it('SSE 스트림 요청을 위해 raw Response를 그대로 반환한다 (자동 파싱하지 않음)', async () => {
      const response = new Response('data: [DONE]\n\n', { status: 200 })
      vi.mocked(fetch).mockResolvedValue(response)

      const controller = new AbortController()
      const result = await conversationApi.chatStream(
        [{ role: 'user', content: 'hi' }],
        'general_english',
        controller.signal
      )

      expect(result).toBe(response)
      const [url, init] = vi.mocked(fetch).mock.calls[0]!
      expect(url).toBe('/api/v1/conversations/chat')
      expect(init!.signal).toBe(controller.signal)
      expect(JSON.parse(init!.body as string)).toEqual({
        messages: [{ role: 'user', content: 'hi' }],
        topic_id: 'general_english',
        wrap_up: false,
        mode: 'practice',
      })
    })

    it('wrapUp을 true로 전달하면 body에 wrap_up: true를 포함한다', async () => {
      vi.mocked(fetch).mockResolvedValue(new Response('data: [DONE]\n\n', { status: 200 }))

      await conversationApi.chatStream(
        [{ role: 'user', content: 'hi' }],
        'general_english',
        new AbortController().signal,
        true
      )

      const [, init] = vi.mocked(fetch).mock.calls[0]!
      expect(JSON.parse(init!.body as string)).toMatchObject({ wrap_up: true })
    })

    it('mode를 live로 전달하면 body에 mode: live를 포함한다', async () => {
      vi.mocked(fetch).mockResolvedValue(new Response('data: [DONE]\n\n', { status: 200 }))

      await conversationApi.chatStream(
        [{ role: 'user', content: 'hi' }],
        'general_english',
        new AbortController().signal,
        false,
        'live'
      )

      const [, init] = vi.mocked(fetch).mock.calls[0]!
      expect(JSON.parse(init!.body as string)).toMatchObject({ mode: 'live' })
    })
  })

  describe('analyze', () => {
    it('성공 시 { analysis } 를 반환하고 messages를 JSON body로 전달한다', async () => {
      vi.mocked(fetch).mockResolvedValue(
        new Response(JSON.stringify({ analysis: '좋은 피드백입니다.' }), { status: 200 })
      )

      const result = await conversationApi.analyze([{ role: 'user', content: 'hi' }])

      expect(result).toEqual({ analysis: '좋은 피드백입니다.' })
      const [url, init] = vi.mocked(fetch).mock.calls[0]!
      expect(url).toBe('/api/v1/conversations/analysis')
      expect(JSON.parse(init!.body as string)).toEqual({
        messages: [{ role: 'user', content: 'hi' }],
      })
    })

    it('403이면 재시도하지 않고 ApiError를 던진다', async () => {
      vi.mocked(fetch).mockResolvedValue(
        new Response(JSON.stringify({ error: 'feature_not_allowed' }), { status: 403 })
      )

      await expect(conversationApi.analyze([])).rejects.toBeInstanceOf(ApiError)
      expect(fetch).toHaveBeenCalledTimes(1)
    })
  })
})
