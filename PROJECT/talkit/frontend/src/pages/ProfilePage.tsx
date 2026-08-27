import { useEffect, useState } from 'react'
import {
  User,
  Mail,
  Phone,
  CalendarDays,
  Sparkles,
  Check,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { InterestPicker } from '@/components/common/InterestPicker'
import { PlanList } from '@/components/membership/PlanList'
import { PaymentModal } from '@/components/membership/PaymentModal'
import { ErrorBanner } from '@/components/common/ErrorBanner'
import { PageHeader } from '@/components/common/PageHeader'
import { useProfileQuery } from '@/hooks/queries/useProfileQuery'
import { useMembershipQuery } from '@/hooks/queries/useMembershipQuery'
import { useExpiredMembershipQuery } from '@/hooks/queries/useExpiredMembershipQuery'
import { usePlansQuery } from '@/hooks/queries/usePlansQuery'
import { useInterestsQuery } from '@/hooks/queries/useInterestsQuery'
import { useUpdateInterestsMutation } from '@/hooks/queries/useUpdateInterestsMutation'
import { formatDate } from '@/lib/utils'
import { FEATURE_LABELS } from '@/lib/constants'
import type { MembershipPlan } from '@/types/membership'

function sameInterests(a: string[], b: string[]): boolean {
  return JSON.stringify([...a].sort()) === JSON.stringify([...b].sort())
}

export function ProfilePage() {
  const { data: profile, isLoading: profileLoading } = useProfileQuery()
  const {
    data: membership,
    isLoading: membershipLoading,
    refetch: refetchMembership,
  } = useMembershipQuery()
  const { data: expiredMembership } = useExpiredMembershipQuery()
  const { data: savedInterests, isLoading: interestsLoading } = useInterestsQuery()
  const { mutate, isPending, isSuccess, reset } = useUpdateInterestsMutation()

  const [selected, setSelected] = useState<string[]>([])
  const [showPlanChange, setShowPlanChange] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<MembershipPlan | null>(null)

  const {
    data: plans,
    isLoading: plansLoading,
    isError: plansError,
    refetch: refetchPlans,
  } = usePlansQuery()

  useEffect(() => {
    if (savedInterests) setSelected(savedInterests)
  }, [savedInterests])

  const toggle = (topicId: string) => {
    reset()
    setSelected((prev) =>
      prev.includes(topicId) ? prev.filter((id) => id !== topicId) : [...prev, topicId]
    )
  }

  const hasChanges = savedInterests ? !sameInterests(selected, savedInterests) : selected.length > 0

  return (
    <div className="min-h-screen bg-background">
      <PageHeader icon={User} title="내 프로필" />

      <main className="container max-w-2xl space-y-8 py-8">
        {/* ── 나의 정보 ── */}
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">나의 정보</h2>
          <Card>
            <CardContent className="space-y-3 pt-6">
              {profileLoading ? (
                <>
                  <Skeleton className="h-4 w-40" />
                  <Skeleton className="h-4 w-56" />
                  <Skeleton className="h-4 w-36" />
                </>
              ) : profile ? (
                <>
                  <div className="flex items-center gap-2 text-sm">
                    <User className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="font-medium">{profile.name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Mail className="h-3.5 w-3.5" />
                    {profile.email}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Phone className="h-3.5 w-3.5" />
                    {profile.phone_number}
                  </div>
                </>
              ) : null}
            </CardContent>
          </Card>
        </section>

        {/* ── 요금제 정보 ── */}
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">요금제 정보</h2>
          <Card>
            <CardContent className="space-y-3 pt-6">
              {membershipLoading ? (
                <Skeleton className="h-20 w-full" />
              ) : membership ? (
                <>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-green-600" />
                      <span className="font-medium">{membership.plan.name}</span>
                      <Badge variant="success">활성</Badge>
                    </div>
                    <Badge variant="secondary">{membership.days_remaining}일 남음</Badge>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {membership.plan.features.map((feature) => (
                      <Badge key={feature} variant="outline" className="text-xs">
                        {FEATURE_LABELS[feature] ?? feature}
                      </Badge>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <CalendarDays className="h-3.5 w-3.5" />
                    {formatDate(membership.starts_at)} ~ {formatDate(membership.expires_at)}
                  </div>
                </>
              ) : expiredMembership ? (
                <>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-muted-foreground">
                        {expiredMembership.plan.name}
                      </span>
                      <Badge variant="outline">만료됨</Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <CalendarDays className="h-3.5 w-3.5" />
                    {formatDate(expiredMembership.starts_at)} ~ {formatDate(expiredMembership.expires_at)}
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">활성 멤버십이 없습니다.</p>
              )}
            </CardContent>
          </Card>

          {/* ── 요금제 변경(토글) — 홈 화면에서 옮겨온 구매/업그레이드 경로 ── */}
          <Button
            variant="outline"
            className="w-full justify-between"
            onClick={() => setShowPlanChange((v) => !v)}
          >
            요금제 변경
            {showPlanChange ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>

          {showPlanChange && (
            <div className="space-y-3 pt-1">
              <p className="text-sm text-muted-foreground">
                플랜 구매 시 기존 멤버십은 자동으로 교체됩니다.
              </p>
              {plansError ? (
                <ErrorBanner
                  message="요금제 목록을 불러오지 못했습니다."
                  onRetry={() => refetchPlans()}
                />
              ) : (
                <PlanList
                  plans={plans}
                  isLoading={plansLoading}
                  currentMembership={membership ?? null}
                  onSelectPlan={setSelectedPlan}
                />
              )}
            </div>
          )}
        </section>

        {/* ── 관심 주제 (언제든 수정 가능) ── */}
        <section className="space-y-3">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold">관심 주제</h2>
            <p className="text-sm text-muted-foreground">
              AI 튜터가 대화 중 활용할 관심 주제예요. 언제든 바꿀 수 있어요.
            </p>
          </div>

          {interestsLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : (
            <>
              <InterestPicker selected={selected} onToggle={toggle} />
              <Button className="w-full" disabled={!hasChanges || isPending} onClick={() => mutate(selected)}>
                {isPending ? (
                  '저장 중...'
                ) : isSuccess && !hasChanges ? (
                  <span className="flex items-center justify-center gap-1.5">
                    <Check className="h-4 w-4" />
                    저장됨
                  </span>
                ) : (
                  '저장하기'
                )}
              </Button>
            </>
          )}
        </section>
      </main>

      {/* ── 결제 모달 ── */}
      <PaymentModal
        plan={selectedPlan}
        open={!!selectedPlan}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedPlan(null)
            void refetchMembership()
          }
        }}
      />
    </div>
  )
}
