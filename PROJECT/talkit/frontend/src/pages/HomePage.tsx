import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, User, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { ActiveMembershipCard } from '@/components/membership/ActiveMembershipCard'
import { PlanList } from '@/components/membership/PlanList'
import { PaymentModal } from '@/components/membership/PaymentModal'
import { ErrorBanner } from '@/components/common/ErrorBanner'
import { useMembershipQuery } from '@/hooks/queries/useMembershipQuery'
import { usePlansQuery } from '@/hooks/queries/usePlansQuery'
import { useSignupMutation } from '@/hooks/queries/useSignupMutation'
import { useLoginMutation } from '@/hooks/queries/useLoginMutation'
import { useUserStore } from '@/stores/userStore'
import { ApiError } from '@/services/apiClient'
import { extractErrorMessage } from '@/lib/networkError'
import type { MembershipPlan } from '@/types/membership'

const EMAIL_REGEXP = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

type AuthComplete = (user: { id: number; name: string }) => void

// ─── 이메일 + 비밀번호로 로그인 ────────────────────────────────────────────
function LoginForm({
  onComplete,
  initialEmail = '',
}: {
  onComplete: AuthComplete
  initialEmail?: string
}) {
  const [email, setEmail] = useState(initialEmail)
  const [password, setPassword] = useState('')
  const [touched, setTouched] = useState(false)
  const { mutate, isPending, isError, error, reset } = useLoginMutation()

  const isValidFormat = EMAIL_REGEXP.test(email.trim())
  const isValid = isValidFormat && password.length > 0

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setTouched(true)
    if (!isValid) return

    mutate(
      { email: email.trim(), password },
      { onSuccess: (data) => onComplete({ id: data.user.id, name: data.user.name }) }
    )
  }

  const errorMessage =
    error instanceof ApiError
      ? error.body.error === 'invalid_credentials'
        ? '이메일 또는 비밀번호가 올바르지 않습니다.'
        : (error.body.message ?? '로그인에 실패했습니다.')
      : '로그인 중 오류가 발생했습니다.'

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="login-email">이메일</Label>
        <Input
          id="login-email"
          type="email"
          placeholder="이메일을 입력해주세요"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            setTouched(false)
            if (isError) reset()
          }}
          className={touched && !isValidFormat ? 'border-destructive' : ''}
        />
        {touched && !isValidFormat && (
          <p className="text-xs text-destructive">
            올바른 이메일 형식으로 입력해주세요. (예: 123@gmail.com)
          </p>
        )}
      </div>
      <div className="space-y-2">
        <Label htmlFor="login-password">비밀번호</Label>
        <Input
          id="login-password"
          type="password"
          placeholder="비밀번호를 입력해주세요"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value)
            if (isError) reset()
          }}
        />
        {isError && <p className="text-xs text-destructive">{errorMessage}</p>}
      </div>
      <Button type="submit" className="w-full" disabled={isPending || !isValid}>
        {isPending ? '확인 중...' : '로그인'}
      </Button>
    </form>
  )
}

const MIN_PASSWORD_LENGTH = 8

// ─── 신규 가입 — 가입 완료 후 로그인 화면으로 이동 ────────────────────────────
function SignupForm({ onSignupSuccess }: { onSignupSuccess: (email: string) => void }) {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirmation, setPasswordConfirmation] = useState('')
  const [touched, setTouched] = useState(false)
  const { mutate, isPending, isError, error, reset } = useSignupMutation()

  const isValidEmail = EMAIL_REGEXP.test(email.trim())
  const isValidPassword = password.length >= MIN_PASSWORD_LENGTH
  const passwordsMatch = password === passwordConfirmation
  const isValid =
    isValidEmail &&
    name.trim() !== '' &&
    phoneNumber.trim() !== '' &&
    isValidPassword &&
    passwordsMatch

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setTouched(true)
    if (!isValid) return

    const trimmedEmail = email.trim()
    mutate(
      { email: trimmedEmail, name: name.trim(), phone_number: phoneNumber.trim(), password },
      { onSuccess: () => onSignupSuccess(trimmedEmail) }
    )
  }

  const errorMessage = extractErrorMessage(
    error,
    '가입에 실패했습니다.',
    '가입 중 오류가 발생했습니다. 다시 시도해주세요.'
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="signup-email">이메일</Label>
        <Input
          id="signup-email"
          type="email"
          placeholder="123@gmail.com"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            if (isError) reset()
          }}
          className={touched && !isValidEmail ? 'border-destructive' : ''}
        />
        {touched && !isValidEmail && (
          <p className="text-xs text-destructive">
            올바른 이메일 형식으로 입력해주세요. (예: 123@gmail.com)
          </p>
        )}
      </div>
      <div className="space-y-2">
        <Label htmlFor="signup-name">이름</Label>
        <Input
          id="signup-name"
          placeholder="홍길동"
          value={name}
          onChange={(e) => {
            setName(e.target.value)
            if (isError) reset()
          }}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="signup-phone">전화번호</Label>
        <Input
          id="signup-phone"
          type="tel"
          placeholder="010-1234-5678"
          value={phoneNumber}
          onChange={(e) => {
            setPhoneNumber(e.target.value)
            if (isError) reset()
          }}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="signup-password">비밀번호</Label>
        <Input
          id="signup-password"
          type="password"
          placeholder="8자 이상 입력해주세요"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value)
            if (isError) reset()
          }}
          className={touched && !isValidPassword ? 'border-destructive' : ''}
        />
        {touched && !isValidPassword && (
          <p className="text-xs text-destructive">비밀번호는 8자 이상이어야 합니다.</p>
        )}
      </div>
      <div className="space-y-2">
        <Label htmlFor="signup-password-confirmation">비밀번호 확인</Label>
        <Input
          id="signup-password-confirmation"
          type="password"
          placeholder="비밀번호를 다시 입력해주세요"
          value={passwordConfirmation}
          onChange={(e) => {
            setPasswordConfirmation(e.target.value)
            if (isError) reset()
          }}
          className={touched && !passwordsMatch ? 'border-destructive' : ''}
        />
        {touched && !passwordsMatch && (
          <p className="text-xs text-destructive">비밀번호가 일치하지 않습니다.</p>
        )}
      </div>

      {isError && <p className="text-xs text-destructive">{errorMessage}</p>}

      <Button type="submit" className="w-full" disabled={isPending || !isValid}>
        {isPending ? '가입 처리 중...' : '가입하기'}
      </Button>
    </form>
  )
}

// ─── 로그인 / 가입 전환 ───────────────────────────────────────────────────────
function UserIdSetup({ onComplete }: { onComplete: AuthComplete }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [prefillEmail, setPrefillEmail] = useState('')
  const [justSignedUp, setJustSignedUp] = useState(false)

  const handleSignupSuccess = (email: string) => {
    setPrefillEmail(email)
    setJustSignedUp(true)
    setMode('login')
  }

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="rounded-full bg-primary/10 p-4">
              <User className="h-8 w-8 text-primary" />
            </div>
          </div>
          <h2 className="text-xl font-semibold">{mode === 'login' ? '로그인' : '회원가입'}</h2>
          <p className="text-sm text-muted-foreground">
            {mode === 'signup' && '이메일, 이름, 전화번호, 비밀번호로 새 계정을 만듭니다.'}
          </p>
        </div>

        {mode === 'login' && justSignedUp && (
          <p className="rounded-md bg-primary/10 px-3 py-2 text-center text-sm text-primary">
            가입이 완료되었습니다. 로그인해주세요.
          </p>
        )}

        {mode === 'login' ? (
          <LoginForm onComplete={onComplete} initialEmail={prefillEmail} />
        ) : (
          <SignupForm onSignupSuccess={handleSignupSuccess} />
        )}

        <p className="text-center text-sm text-muted-foreground">
          {mode === 'login' ? (
            <>
              계정이 없으신가요?{' '}
              <button
                type="button"
                className="font-medium text-primary underline-offset-4 hover:underline"
                onClick={() => {
                  setJustSignedUp(false)
                  setMode('signup')
                }}
              >
                가입하기
              </button>
            </>
          ) : (
            <>
              이미 계정이 있으신가요?{' '}
              <button
                type="button"
                className="font-medium text-primary underline-offset-4 hover:underline"
                onClick={() => {
                  setJustSignedUp(false)
                  setMode('login')
                }}
              >
                로그인
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  )
}

// ─── 메인 홈 콘텐츠 ──────────────────────────────────────────────────────────
function HomeContent() {
  const [selectedPlan, setSelectedPlan] = useState<MembershipPlan | null>(null)

  const {
    data: membership,
    isLoading: membershipLoading,
    isError: membershipError,
    refetch: refetchMembership,
  } = useMembershipQuery()

  const {
    data: plans,
    isLoading: plansLoading,
    isError: plansError,
    refetch: refetchPlans,
  } = usePlansQuery()

  // 이미 활성 멤버십이 있으면 홈 화면에서는 요금제 선택을 더 보여주지 않는다 —
  // 변경/연장은 프로필(이름 뱃지 클릭) 페이지의 "요금제 변경" 토글로 옮겨졌다.
  // 아직 결제 전(membership === null)이거나 로딩 중에는 기존 화면을 그대로 유지한다.
  const showPlanSection = !membershipLoading && !membership

  // 멤버십이 없는 게 확실할 때(로딩/에러가 아님)는 "내 멤버십" 구간 자체를 보여주지 않는다.
  // 로딩 중이거나 에러일 때는 스켈레톤/재시도 UI를 위해 계속 표시한다.
  const showMembershipSection = membershipLoading || membershipError || !!membership

  return (
    <div className="space-y-8">
      {/* ── 내 멤버십 ── */}
      {showMembershipSection && (
        <section>
          <h2 className="mb-4 text-lg font-semibold">내 멤버십</h2>
          {membershipError ? (
            <ErrorBanner
              message="멤버십 정보를 불러오지 못했습니다."
              onRetry={() => refetchMembership()}
            />
          ) : (
            <ActiveMembershipCard
              membership={membership ?? null}
              isLoading={membershipLoading}
            />
          )}
        </section>
      )}

      {showPlanSection && (
        <>
          <Separator />

          {/* ── 요금제 선택 ── */}
          <section>
            <div className="mb-4 space-y-1">
              <h2 className="text-lg font-semibold">요금제 선택</h2>
              <p className="text-sm text-muted-foreground">
                플랜 구매 시 기존 멤버십은 자동으로 교체됩니다.
              </p>
            </div>

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
          </section>
        </>
      )}

      {/* ── 결제 모달 ── */}
      <PaymentModal
        plan={selectedPlan}
        open={!!selectedPlan}
        onOpenChange={(open) => !open && setSelectedPlan(null)}
      />
    </div>
  )
}

// ─── 페이지 루트 ──────────────────────────────────────────────────────────────
export function HomePage() {
  const { userId, userName, setUser, clearUser } = useUserStore()
  const { data: membership } = useMembershipQuery()

  return (
    <div className="min-h-screen bg-background">
      {/* ── 헤더 ── */}
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="container flex h-14 max-w-2xl items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <span className="font-semibold">Talkit</span>
          </div>

          {userId !== null && (
            <div className="flex items-center gap-3">
              <Link to="/profile">
                <Badge
                  variant="secondary"
                  className="gap-1 cursor-pointer transition-colors hover:bg-secondary/70"
                >
                  <User className="h-3 w-3" />
                  {userName ?? `User ${userId}`}
                </Badge>
              </Link>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearUser}
                className="text-muted-foreground"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* ── 본문 ── */}
      <main className="container max-w-2xl py-8">
        {userId === null ? (
          <UserIdSetup onComplete={setUser} />
        ) : (
          <>
            <div className="mb-8 space-y-1">
              <h1 className="text-2xl font-bold">AI 영어 튜터</h1>
              <p className="text-sm text-muted-foreground">
                {membership
                  ? '원어민 AI 튜터와 영어 대화를 시작해보세요.'
                  : '멤버십을 구매하고 원어민 AI 튜터와 영어 대화를 시작하세요.'}
              </p>
            </div>
            <HomeContent />
          </>
        )}
      </main>
    </div>
  )
}
