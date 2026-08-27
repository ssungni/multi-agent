import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { InterestPicker } from '@/components/common/InterestPicker'
import { PageHeader } from '@/components/common/PageHeader'
import { useInterestsQuery } from '@/hooks/queries/useInterestsQuery'
import { useUpdateInterestsMutation } from '@/hooks/queries/useUpdateInterestsMutation'

export function TutorTopicSelectPage() {
  const navigate = useNavigate()
  const { data: savedInterests, isLoading } = useInterestsQuery()
  const { mutate, isPending } = useUpdateInterestsMutation()
  const [selected, setSelected] = useState<string[]>([])

  // 이미 관심사를 저장해둔 유저는 선택 화면을 건너뛰고 바로 대화로 들어간다.
  // hasRedirectedRef로 React.StrictMode가 dev에서 이 effect를 두 번 실행하더라도
  // navigate()가 한 번만 호출되게 막는다 — 안 그러면 /chat으로 두 번 내비게이션되면서
  // ChatPage가 실제로 두 번 마운트되어, 첫 인사 TTS 요청이 중간에 취소되는 문제가 있었다.
  const hasRedirectedRef = useRef(false)
  useEffect(() => {
    if (!isLoading && savedInterests && savedInterests.length > 0 && !hasRedirectedRef.current) {
      hasRedirectedRef.current = true
      navigate('/chat', { replace: true })
    }
  }, [isLoading, savedInterests, navigate])

  const toggle = (topicId: string) => {
    setSelected((prev) =>
      prev.includes(topicId) ? prev.filter((id) => id !== topicId) : [...prev, topicId]
    )
  }

  const handleSubmit = () => {
    if (selected.length === 0) return
    mutate(selected, { onSuccess: () => navigate('/chat') })
  }

  if (isLoading || (savedInterests && savedInterests.length > 0)) return null

  return (
    <div className="min-h-screen bg-background">
      <PageHeader icon={MessageCircle} title="AI 튜터" />

      <main className="container max-w-2xl space-y-6 py-8">
        <div className="space-y-1 text-center">
          <h1 className="text-xl font-semibold">관심 있는 주제를 골라주세요</h1>
          <p className="text-sm text-muted-foreground">
            여러 개 선택할 수 있어요. AI 튜터가 대화 중 자연스럽게 이 주제들로 질문을 건네요.
            (나중에 프로필에서 언제든 수정할 수 있어요.)
          </p>
        </div>

        <InterestPicker selected={selected} onToggle={toggle} />

        <Button
          className="w-full"
          disabled={selected.length === 0 || isPending}
          onClick={handleSubmit}
        >
          {isPending ? '저장 중...' : `대화 시작하기${selected.length > 0 ? ` (${selected.length})` : ''}`}
        </Button>
      </main>
    </div>
  )
}
