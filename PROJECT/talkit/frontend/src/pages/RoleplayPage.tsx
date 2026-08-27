import { useNavigate } from 'react-router-dom'
import { Users, ChevronRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorBanner } from '@/components/common/ErrorBanner'
import { PageHeader } from '@/components/common/PageHeader'
import { useRoleplayScenariosQuery } from '@/hooks/queries/useRoleplayScenariosQuery'
import type { RoleplayScenario } from '@/types/roleplay'

function groupBySeries(scenarios: RoleplayScenario[]): Array<[string, RoleplayScenario[]]> {
  const groups = new Map<string, RoleplayScenario[]>()
  for (const scenario of scenarios) {
    const list = groups.get(scenario.series_title) ?? []
    list.push(scenario)
    groups.set(scenario.series_title, list)
  }
  return Array.from(groups.entries())
}

function ScenarioRowSkeleton() {
  return (
    <div className="flex items-center gap-3 rounded-lg border p-4">
      <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-3 w-56" />
      </div>
    </div>
  )
}

export function RoleplayPage() {
  const navigate = useNavigate()
  const { data: scenarios, isLoading, isError, refetch } = useRoleplayScenariosQuery()

  const handleStart = (scenario: RoleplayScenario) => {
    navigate('/chat', {
      state: {
        topicId: scenario.topic_id,
        opening: scenario.opening,
        liveOpening: scenario.live_opening,
      },
    })
  }

  return (
    <div className="min-h-screen bg-background">
      <PageHeader icon={Users} title="AI 롤플레이" />

      <main className="container max-w-2xl space-y-8 py-6">
        {isError ? (
          <ErrorBanner message="롤플레이 시나리오를 불러오지 못했습니다." onRetry={() => refetch()} />
        ) : isLoading ? (
          <div className="space-y-3">
            <ScenarioRowSkeleton />
            <ScenarioRowSkeleton />
          </div>
        ) : !scenarios || scenarios.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            이용 가능한 시나리오가 없습니다.
          </p>
        ) : (
          groupBySeries(scenarios).map(([seriesTitle, items]) => (
            <section key={seriesTitle} className="space-y-3">
              <div className="space-y-1">
                <h2 className="text-lg font-semibold">{seriesTitle}</h2>
              </div>
              <div className="space-y-2">
                {items.map((scenario) => (
                  <button
                    key={scenario.id}
                    type="button"
                    onClick={() => handleStart(scenario)}
                    className="flex w-full items-center gap-3 rounded-lg border p-4 text-left transition-colors hover:bg-muted/50"
                  >
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                      {String(scenario.position).padStart(2, '0')}
                    </span>
                    <div className="min-w-0 flex-1 space-y-1">
                      <span className="block truncate text-sm font-medium">{scenario.title}</span>
                      <p className="truncate text-xs text-muted-foreground">{scenario.description}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </section>
          ))
        )}
      </main>
    </div>
  )
}
