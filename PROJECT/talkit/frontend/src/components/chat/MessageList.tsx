import { useEffect, useRef } from 'react'
import { ChatBubble } from './ChatBubble'
import type { Message } from '@/types/conversation'

interface MessageListProps {
  messages: Message[]
  streamingContent: string
}

// 대화 메시지 목록을 렌더링하고, 새 메시지/스트리밍 내용이 생길 때마다 맨 아래로 자동 스크롤한다.
export function MessageList({ messages, streamingContent }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // 메시지 개수나 스트리밍 중인 응답 내용이 바뀔 때마다 최신 메시지가 보이도록 스크롤을 맨 아래로 이동
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, streamingContent])

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-4">
      {messages.length === 0 && !streamingContent && (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-muted-foreground">AI 튜터가 인사말을 시작합니다...</p>
        </div>
      )}

      {messages.map((msg) => (
        <ChatBubble key={msg.id} message={msg} />
      ))}

      {/* LLM 응답이 아직 완성되지 않고 스트리밍 중일 때 임시 말풍선으로 보여준다 */}
      {streamingContent && (
        <ChatBubble
          message={{
            id: '__streaming__',
            role: 'assistant',
            content: streamingContent,
            isStreaming: true,
          }}
        />
      )}

      <div ref={bottomRef} />
    </div>
  )
}
