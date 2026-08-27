import { useState } from 'react'
import { BookOpen } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ErrorBanner } from '@/components/common/ErrorBanner'
import { PageHeader } from '@/components/common/PageHeader'
import { useTopicsQuery } from '@/hooks/queries/useTopicsQuery'
import type { Topic } from '@/types/topic'

// 이미지를 카드 전체 배경으로 깔고, 카테고리 텍스트만 이미지 위에 겹쳐서 보여준다
// (제목/난이도 배지는 카드에 노출하지 않음 — 상세 다이얼로그에서만 보여준다).
function TopicCard({ topic, onSelect }: { topic: Topic; onSelect: (topic: Topic) => void }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(topic)}
      className="group relative aspect-square overflow-hidden rounded-lg"
    >
      <img
        src={topic.image_url}
        alt={topic.category}
        className="h-full w-full object-cover transition-transform group-hover:scale-105"
        loading="lazy"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/0 to-transparent" />
      <span className="absolute bottom-2 left-2.5 text-sm font-semibold text-white drop-shadow-sm">
        {topic.category}
      </span>
    </button>
  )
}

function TopicCardSkeleton() {
  return <Skeleton className="aspect-square w-full rounded-lg" />
}

// 영어 단락 + 한국어 번역을 한 묶음으로 보여주는 블록
function ReadingParagraph({ english, korean }: { english: string; korean: string }) {
  return (
    <div className="space-y-1.5 rounded-lg bg-muted/40 p-3">
      <p className="text-sm leading-relaxed">{english}</p>
      <p className="text-sm leading-relaxed text-muted-foreground">{korean}</p>
    </div>
  )
}

export function TopicPage() {
  const [selected, setSelected] = useState<Topic | null>(null)
  const { data: topics, isLoading, isError, refetch } = useTopicsQuery()

  return (
    <div className="min-h-screen bg-background">
      <PageHeader icon={BookOpen} title="토픽" />

      <main className="container max-w-2xl space-y-4 py-6">
        {isError ? (
          <ErrorBanner message="토픽 목록을 불러오지 못했습니다." onRetry={() => refetch()} />
        ) : isLoading ? (
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <TopicCardSkeleton key={i} />
            ))}
          </div>
        ) : !topics || topics.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">표시할 토픽이 없습니다.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {topics.map((topic) => (
              <TopicCard key={topic.id} topic={topic} onSelect={setSelected} />
            ))}
          </div>
        )}
      </main>

      <Dialog open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
          {selected && (
            <>
              <img
                src={selected.image_url}
                alt={selected.title}
                className="max-h-48 w-full rounded-md object-cover"
              />
              <DialogHeader>
                <Badge variant="secondary" className="w-fit text-xs">
                  {selected.category}
                </Badge>
                <DialogTitle>{selected.title}</DialogTitle>
              </DialogHeader>

              <div className="space-y-3">
                <ReadingParagraph english={selected.english_1} korean={selected.korean_1} />
                <ReadingParagraph english={selected.english_2} korean={selected.korean_2} />
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
