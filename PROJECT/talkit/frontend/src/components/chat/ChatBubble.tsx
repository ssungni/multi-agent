import { cn } from '@/lib/utils'
import { AudioPlayer } from './AudioPlayer'
import type { Message } from '@/types/conversation'

interface ChatBubbleProps {
  message: Message
}

// 사용자/AI 메시지 하나를 말풍선 형태로 렌더링하는 컴포넌트
export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === 'user'

  return (
    // 발화자에 따라 말풍선을 좌/우로 정렬하고 색상을 다르게 표시
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'relative max-w-[75%] rounded-2xl px-4 py-3 text-sm shadow-sm',
          isUser
            ? 'rounded-br-sm bg-primary text-primary-foreground'
            : 'rounded-bl-sm bg-muted text-foreground'
        )}
      >
        <p className="whitespace-pre-wrap leading-relaxed">
          {message.content}
          {/* 스트리밍 중인 AI 응답에는 깜빡이는 커서를 표시해 아직 입력 중임을 나타낸다 */}
          {message.isStreaming && (
            <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-current opacity-70" />
          )}
        </p>

        {/* 메시지에 연결된 오디오가 있으면 다시 듣기 버튼을 노출 */}
        {message.audioUrls && message.audioUrls.length > 0 && (
          <div className="mt-1.5 flex justify-end">
            <AudioPlayer audioUrls={message.audioUrls} />
          </div>
        )}
      </div>
    </div>
  )
}
