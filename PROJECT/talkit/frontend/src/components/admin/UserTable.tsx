import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDate } from '@/lib/utils'
import type { AdminUser } from '@/types/admin'

interface UserTableProps {
  users: AdminUser[] | undefined
  isLoading: boolean
  onGrant: (user: AdminUser) => void
  onRevoke: (membershipId: number) => void
  revokingId?: number | null
}

function UserRowSkeleton() {
  return (
    <div className="flex items-center justify-between p-4">
      <div className="space-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-44" />
      </div>
      <Skeleton className="h-8 w-20" />
    </div>
  )
}

export function UserTable({ users, isLoading, onGrant, onRevoke, revokingId }: UserTableProps) {
  if (isLoading) {
    return (
      <div className="divide-y rounded-lg border">
        <UserRowSkeleton />
        <UserRowSkeleton />
        <UserRowSkeleton />
      </div>
    )
  }

  if (!users || users.length === 0) {
    return (
      <p className="rounded-lg border border-dashed py-8 text-center text-sm text-muted-foreground">
        등록된 유저가 없습니다.
      </p>
    )
  }

  return (
    <div className="divide-y rounded-lg border">
      {users.map((user) => {
        const membership = user.active_membership
        return (
          <div key={user.id} className="flex items-center justify-between gap-4 p-4">
            <div className="min-w-0 space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-medium">{user.name}</span>
                <span className="text-xs text-muted-foreground">#{user.id}</span>
              </div>
              <p className="truncate text-sm text-muted-foreground">{user.email}</p>
              {membership ? (
                <Badge variant="success" className="gap-1">
                  {membership.plan_name} · {formatDate(membership.expires_at)} 만료
                </Badge>
              ) : user.expired_membership ? (
                <Badge variant="outline" className="gap-1">
                  {user.expired_membership.plan_name} · {formatDate(user.expired_membership.expires_at)} 만료됨
                </Badge>
              ) : (
                <Badge variant="outline">활성 멤버십 없음</Badge>
              )}
            </div>

            <div className="flex shrink-0 gap-2">
              <Button
                size="sm"
                className="bg-gray-700 text-white hover:bg-gray-800"
                onClick={() => onGrant(user)}
              >
                {membership ? '교체' : '부여'}
              </Button>
              {membership && (
                <Button
                  size="sm"
                  className="bg-green-600 text-white hover:bg-green-700"
                  disabled={revokingId === membership.id}
                  onClick={() => onRevoke(membership.id)}
                >
                  {revokingId === membership.id ? '삭제 중...' : '삭제'}
                </Button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
