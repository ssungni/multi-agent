import { useState } from 'react'
import { ShieldCheck, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ErrorBanner } from '@/components/common/ErrorBanner'
import { PageHeader } from '@/components/common/PageHeader'
import { UserTable } from '@/components/admin/UserTable'
import { GrantMembershipModal } from '@/components/admin/GrantMembershipModal'
import { useAdminUsersQuery } from '@/hooks/queries/useAdminUsersQuery'
import { useRevokeMembershipMutation } from '@/hooks/queries/useRevokeMembershipMutation'
import { useVerifyAdminTokenMutation } from '@/hooks/queries/useVerifyAdminTokenMutation'
import { useUserStore } from '@/stores/userStore'
import { ApiError } from '@/services/apiClient'
import type { AdminUser } from '@/types/admin'

// ─── 어드민 토큰 입력 ─────────────────────────────────────────────────────────
function AdminTokenSetup() {
  const [input, setInput] = useState('')
  const setAdminToken = useUserStore((s) => s.setAdminToken)
  const { mutate, isPending, isError, reset } = useVerifyAdminTokenMutation()

  // 토큰이 실제로 유효한지 먼저 확인한 뒤에만 스토어에 커밋한다 —
  // 틀린 토큰으로 화면이 바뀌었다가 에러가 나는 대신, 이 화면에서 바로 알려준다.
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const token = input.trim()
    if (!token) return

    mutate(token, {
      onSuccess: () => setAdminToken(token),
    })
  }

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="rounded-full bg-primary/10 p-4">
              <ShieldCheck className="h-8 w-8 text-primary" />
            </div>
          </div>
          <h2 className="text-xl font-semibold">어드민 토큰 입력</h2>
          <p className="text-sm text-muted-foreground">
            X-Admin-Token 헤더로 사용할 값을 입력하세요.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="admin-token">Admin Token</Label>
            <Input
              id="admin-token"
              type="password"
              placeholder="어드민 토큰을 입력해주세요"
              value={input}
              onChange={(e) => {
                setInput(e.target.value)
                if (isError) reset()
              }}
              autoComplete="off"
            />
            {isError && (
              <p className="text-xs text-destructive">토큰 값이 잘못되었습니다.</p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={isPending || !input.trim()}>
            {isPending ? '확인 중...' : '입장하기'}
          </Button>
        </form>
      </div>
    </div>
  )
}

// ─── 토큰 확인 후 본문 ────────────────────────────────────────────────────────
function AdminContent() {
  const setAdminToken = useUserStore((s) => s.setAdminToken)
  const [page, setPage] = useState(1)
  const [grantTarget, setGrantTarget] = useState<AdminUser | null>(null)
  const [revokingId, setRevokingId] = useState<number | null>(null)

  const { data, isLoading, isError, error, refetch } = useAdminUsersQuery(page)
  const { mutate: revoke } = useRevokeMembershipMutation()

  const isAuthError = error instanceof ApiError && error.status === 401

  const handleRevoke = (membershipId: number) => {
    if (!window.confirm('이 멤버십을 삭제하시겠습니까?')) return
    setRevokingId(membershipId)
    revoke(membershipId, { onSettled: () => setRevokingId(null) })
  }

  if (isAuthError) {
    return (
      <ErrorBanner
        message="토큰이 올바르지 않습니다. 다시 입력해주세요."
        onRetry={() => setAdminToken('')}
      />
    )
  }

  if (isError) {
    return <ErrorBanner message="유저 목록을 불러오지 못했습니다." onRetry={() => refetch()} />
  }

  const meta = data?.meta
  const hasPrev = (meta?.page ?? 1) > 1
  const hasNext = meta ? meta.page * meta.per_page < meta.total : false

  return (
    <div className="space-y-4">
      <UserTable
        users={data?.users}
        isLoading={isLoading}
        onGrant={setGrantTarget}
        onRevoke={handleRevoke}
        revokingId={revokingId}
      />

      {meta && meta.total > meta.per_page && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            총 {meta.total}명 중 {(meta.page - 1) * meta.per_page + 1}–
            {Math.min(meta.page * meta.per_page, meta.total)}
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={!hasPrev}
              onClick={() => setPage((p) => p - 1)}
            >
              이전
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={!hasNext}
              onClick={() => setPage((p) => p + 1)}
            >
              다음
            </Button>
          </div>
        </div>
      )}

      <GrantMembershipModal
        user={grantTarget}
        open={!!grantTarget}
        onOpenChange={(open) => !open && setGrantTarget(null)}
      />
    </div>
  )
}

// ─── 페이지 루트 ──────────────────────────────────────────────────────────────
export function AdminPage() {
  const { adminToken, setAdminToken } = useUserStore()

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        icon={ShieldCheck}
        title="어드민"
        actions={
          adminToken && (
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground"
              onClick={() => setAdminToken('')}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          )
        }
      />

      <main className="container max-w-2xl space-y-6 py-8">
        {!adminToken ? (
          <AdminTokenSetup />
        ) : (
          <>
            <div className="space-y-1">
              <h1 className="text-2xl font-bold">유저 / 멤버십 관리</h1>
              <p className="text-muted-foreground">유저에게 멤버십을 부여하거나 삭제합니다.</p>
            </div>
            <AdminContent />
          </>
        )}
      </main>
    </div>
  )
}
