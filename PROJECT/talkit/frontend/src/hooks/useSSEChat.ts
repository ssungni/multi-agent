// SSE(Server-Sent Events)로 LLM 응답을 스트리밍 수신하고, 문장 단위로 분리해 콜백으로 전달하는 훅
import { useRef, useCallback } from 'react'
import { conversationApi } from '@/services/conversationApi'
import type { ConversationMode } from '@/types/conversation'

interface SSEChatCallbacks {
  onDelta: (delta: string) => void
  /** Fires for each grammatically complete sentence detected during the stream. */
  onSentence: (sentence: string) => void
  /** Fires when stream ends, passing any trailing text that wasn't a complete sentence. */
  onDone: (remainder: string) => void
  onError: (error: Error) => void
}

export function useSSEChat() {
  const abortRef = useRef<AbortController | null>(null)

  // 채팅 메시지 히스토리를 백엔드로 보내고, SSE 스트림 응답을 델타/문장 단위로 콜백에 전달
  const send = useCallback(
    async (
      messages: Array<{ role: string; content: string }>,
      topicId: string,
      callbacks: SSEChatCallbacks,
      wrapUp = false,
      mode: ConversationMode = 'practice'
    ) => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      try {
        const res = await conversationApi.chatStream(messages, topicId, controller.signal, wrapUp, mode)
        if (!res.ok) throw new Error(`Chat failed: ${res.status}`)

        const reader = res.body!.pipeThrough(new TextDecoderStream()).getReader()
        // Text not yet emitted as a complete sentence — grows with each delta
        let pending = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          for (const line of value.split('\n')) {
            if (!line.startsWith('data: ')) continue
            const data = line.slice(6).trim()

            if (data === '[DONE]') {
              callbacks.onDone(pending.trim())
              return
            }

            try {
              const parsed = JSON.parse(data)
              // 백엔드(ChatController)는 { delta: "..." } 형태로 보낸다.
              // (OpenAI raw chunk 형식이 아니라, 백엔드가 이미 content만 추출해 보냄)
              const delta: string = parsed.delta ?? ''
              if (!delta) continue

              pending += delta
              callbacks.onDelta(delta)

              // Greedily extract all complete sentences that have trailing whitespace
              // (whitespace after punctuation means another sentence is coming)
              // 문장 종결부호(.!?) 뒤에 공백이 오면 다음 문장이 이어진다는 뜻이므로,
              // pending에서 완성된 문장을 모두 꺼내 onSentence로 즉시 전달(병렬 TTS 트리거)
              while (true) {
                const match = pending.match(/^(.+?[.!?])\s+/)
                if (!match) break
                callbacks.onSentence(match[1].trim())
                pending = pending.slice(match[0].length)
              }
            } catch {}
          }
        }

        // Stream closed without [DONE]
        callbacks.onDone(pending.trim())
      } catch (err) {
        if ((err as { name?: string }).name !== 'AbortError') {
          callbacks.onError(err as Error)
        }
      }
    },
    []
  )

  // 진행 중인 스트림 요청을 취소
  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { send, abort }
}
