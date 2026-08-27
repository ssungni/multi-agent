import { useState } from 'react'
import { CheckCircle2, Loader2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { conversationApi } from '@/services/conversationApi'
import type { Message } from '@/types/conversation'

interface EndConversationDialogProps {
  open: boolean
  onConfirm: () => void
  wordCount: number
  durationLabel: string
  messages: Message[]
}

// 발화량이 이 기준보다 적으면 "더 말해보라"는 격려 문구를, 그 이상이면 칭찬 문구를 보여준다
const LOW_WORD_COUNT_THRESHOLD = 20

// 대화 종료 시 요약(단어 수, 대화 시간)과 선택적 AI 분석 결과를 보여주는 다이얼로그
export function EndConversationDialog({
  open,
  onConfirm,
  wordCount,
  durationLabel,
  messages,
}: EndConversationDialogProps) {
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)

  // 사용자가 요청할 때만 대화 전체를 서버로 보내 AI 분석을 받아온다(기본적으로 자동 호출하지 않음)
  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    setAnalysisError(null)
    try {
      const payload = messages.map((m) => ({ role: m.role, content: m.content }))
      const { analysis: result } = await conversationApi.analyze(payload)
      setAnalysis(result)
    } catch {
      setAnalysisError('분석에 실패했습니다. 다시 시도해주세요.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  // 발화량 기준으로 격려/칭찬 문구를 다르게 노출(AI 분석 결과가 없을 때 기본으로 보여줄 내용)
  const tip =
    wordCount < LOW_WORD_COUNT_THRESHOLD
      ? { title: '다음엔 조금만 더 말해주세요.', subtitle: '조금만 더 말하면 핵심 표현을 찾아드려요.' }
      : { title: '오늘 대화 정말 잘하셨어요!', subtitle: '다음에도 이어서 꾸준히 연습해보세요.' }

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onConfirm()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader className="items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          </div>
          <DialogTitle className="text-xl">대화를 완료했어요.</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border bg-muted/30 p-3 text-center">
            <p className="text-xs text-muted-foreground">말한 단어</p>
            <p className="mt-1 text-lg font-semibold">{wordCount}</p>
          </div>
          <div className="rounded-lg border bg-muted/30 p-3 text-center">
            <p className="text-xs text-muted-foreground">대화 시간</p>
            <p className="mt-1 text-lg font-semibold">{durationLabel}</p>
          </div>
        </div>

        {/* AI 분석 결과가 있으면 그것을 우선 보여주고, 없으면 기본 격려/칭찬 문구를 보여준다 */}
        {analysis ? (
          <div className="space-y-1 rounded-lg bg-green-50 p-3">
            <p className="flex items-center gap-1.5 text-xs font-medium text-green-700">
              <Sparkles className="h-3.5 w-3.5" />
              AI 분석 결과
            </p>
            <p className="whitespace-pre-wrap text-sm text-green-900">{analysis}</p>
          </div>
        ) : (
          <div className="space-y-1 rounded-lg bg-muted/50 p-3 text-center">
            <p className="text-sm font-medium">{tip.title}</p>
            <p className="text-xs text-muted-foreground">{tip.subtitle}</p>
          </div>
        )}

        {analysisError && <p className="text-center text-xs text-destructive">{analysisError}</p>}

        <div className="grid grid-cols-2 gap-3">
          {/* 분석 중이거나 이미 분석 결과를 받았으면 재요청을 막는다 */}
          <Button variant="outline" onClick={() => void handleAnalyze()} disabled={isAnalyzing || !!analysis}>
            {isAnalyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : 'AI 분석 요청'}
          </Button>
          <Button onClick={onConfirm}>확인</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
