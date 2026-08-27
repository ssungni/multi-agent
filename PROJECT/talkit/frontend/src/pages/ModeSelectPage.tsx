import { useNavigate } from 'react-router-dom'
import { MessageCircle, MessagesSquare, Phone } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { PageHeader } from '@/components/common/PageHeader'
import { useConversationStore } from '@/stores/conversationStore'
import type { ConversationMode } from '@/types/conversation'

interface ModeOption {
  mode: ConversationMode
  title: string
  description: string
  icon: typeof MessagesSquare
}

const MODE_OPTIONS: ModeOption[] = [
  {
    mode: 'practice',
    title: '연습 모드',
    description: 'AI가 한 말, 내가 한 말 모두 다시 볼 수 있어요!',
    icon: MessagesSquare,
  },
  {
    mode: 'live',
    title: '실전 모드',
    description: 'AI 원어민과 전화하는 느낌을 느껴봐요!',
    icon: Phone,
  },
]

interface ModeSelectPageProps {
  // 모드 선택 후 이동할 경로. AI 튜터는 관심사 선택으로, 롤플레이는 시나리오 목록으로.
  nextPath: string
  headerTitle: string
}

export function ModeSelectPage({ nextPath, headerTitle }: ModeSelectPageProps) {
  const navigate = useNavigate()
  const setMode = useConversationStore((s) => s.setMode)

  const handleSelect = (mode: ConversationMode) => {
    setMode(mode)
    navigate(nextPath)
  }

  return (
    <div className="min-h-screen bg-background">
      <PageHeader icon={MessageCircle} title={headerTitle} />

      <main className="container max-w-2xl space-y-6 py-8">
        <div className="space-y-1 text-center">
          <h1 className="text-xl font-semibold">어떻게 대화해볼까요?</h1>
          <p className="text-sm text-muted-foreground">매번 대화를 시작할 때마다 다시 고를 수 있어요.</p>
        </div>

        <div className="space-y-4">
          {MODE_OPTIONS.map(({ mode, title, description, icon: Icon }) => (
            <Card
              key={mode}
              role="button"
              tabIndex={0}
              onClick={() => handleSelect(mode)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') handleSelect(mode)
              }}
              className="flex cursor-pointer items-center gap-4 p-5 transition-colors hover:bg-muted/50"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-green-100">
                <Icon className="h-6 w-6 text-green-600" />
              </div>
              <div className="space-y-1">
                <p className="font-semibold">{title}</p>
                <p className="text-sm text-muted-foreground">{description}</p>
              </div>
            </Card>
          ))}
        </div>
      </main>
    </div>
  )
}
