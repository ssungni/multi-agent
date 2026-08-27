// AI와의 대화(음성 인식, 음성 합성, 채팅 스트리밍, 대화 분석)를 담당하는 API 서비스
import { API_BASE_URL } from '@/lib/constants'
import { useUserStore } from '@/stores/userStore'
import { apiRequest, apiRequestForm, apiRequestBlob, ApiError } from '@/services/apiClient'
import type { ConversationMode } from '@/types/conversation'

// chatStream은 SSE 스트림을 그대로 반환해야 해서(호출자가 res.ok와 res.body를 직접
// 다룸) apiClient의 공통 함수로는 표현할 수 없다 — 이 경우만 raw fetch를 유지한다.
function getUserHeaders(): Record<string, string> {
  const { userId } = useUserStore.getState()
  return userId !== null ? { 'X-User-Id': String(userId) } : {}
}

// 일시적인 네트워크/서버 오류에 대비해 요청을 재시도하되, 인증/권한/속도 제한 오류는 재시도 없이 즉시 전파
async function withRetry<T>(fn: () => Promise<T>, maxRetries = 2): Promise<T> {
  let lastError: unknown
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (err) {
      lastError = err
      const status = err instanceof ApiError ? err.status : 0
      if (status === 401 || status === 403 || status === 429) throw err
      if (attempt < maxRetries) await new Promise((r) => setTimeout(r, 500 * (attempt + 1)))
    }
  }
  throw lastError
}

export const conversationApi = {
  // 녹음된 음성을 서버에 전송해 텍스트로 변환(STT)
  async stt(audioBlob: Blob, signal?: AbortSignal): Promise<{ text: string }> {
    return withRetry(() => {
      const formData = new FormData()
      // VAD로 무음을 잘라낸 클립은 WAV로 인코딩되어 온다 — Whisper가 파일 확장자로
      // 포맷을 추론하므로, 실제 인코딩에 맞는 확장자를 붙여야 한다.
      const extension = audioBlob.type.includes('wav') ? 'wav' : 'webm'
      formData.append('audio', audioBlob, `recording.${extension}`)
      return apiRequestForm<{ text: string }>('/conversations/stt', formData, { signal })
    })
  },

  // 텍스트를 음성으로 변환(TTS)해 오디오 Blob을 반환
  async tts(text: string, signal?: AbortSignal): Promise<Blob> {
    return withRetry(() =>
      apiRequestBlob('/conversations/tts', {
        method: 'POST',
        body: JSON.stringify({ text }),
        signal,
      })
    )
  },

  // 대화 메시지를 서버로 보내고 AI 응답을 스트리밍으로 받기 위한 요청을 시작
  chatStream(
    messages: Array<{ role: string; content: string }>,
    topicId: string,
    signal: AbortSignal,
    wrapUp = false,
    mode: ConversationMode = 'practice'
  ): Promise<Response> {
    return fetch(`${API_BASE_URL}/conversations/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getUserHeaders() },
      body: JSON.stringify({ messages, topic_id: topicId, wrap_up: wrapUp, mode }),
      signal,
    })
  },

  // 대화 내용을 서버에 보내 학습 분석 결과를 요청
  async analyze(
    messages: Array<{ role: string; content: string }>,
    signal?: AbortSignal
  ): Promise<{ analysis: string }> {
    return withRetry(() =>
      apiRequest<{ analysis: string }>('/conversations/analysis', {
        method: 'POST',
        body: JSON.stringify({ messages }),
        signal,
      })
    )
  },
}
