// 모든 API 요청에서 공통으로 사용하는 fetch 래퍼와 에러 타입, 인증 헤더 처리를 담당
import { API_BASE_URL } from '@/lib/constants'
import { useUserStore } from '@/stores/userStore'
import type { ApiErrorBody } from '@/types/api'

// 서버가 실패 응답을 반환했을 때 상태 코드와 에러 바디를 함께 담아 던지는 에러 타입
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: ApiErrorBody
  ) {
    super(`HTTP ${status}: ${body.error}`)
    this.name = 'ApiError'
  }
}

// 요청 종류(일반/관리자/멀티파트)에 따라 필요한 인증·콘텐츠 타입 헤더를 구성
function getHeaders(
  opts: { admin?: boolean; multipart?: boolean; adminToken?: string } = {}
): Record<string, string> {
  const { userId, adminToken } = useUserStore.getState()
  const headers: Record<string, string> = {}

  if (!opts.multipart) {
    headers['Content-Type'] = 'application/json'
  }
  if (!opts.admin && userId !== null) {
    headers['X-User-Id'] = String(userId)
  }
  // 토큰 검증 등 스토어에 아직 커밋하지 않은 후보 토큰을 써야 하는 경우를 위해
  // 명시적으로 전달된 토큰이 있으면 그것을 우선한다.
  const tokenToUse = opts.adminToken ?? adminToken
  if (opts.admin && tokenToUse) {
    headers['X-Admin-Token'] = tokenToUse
  }
  return headers
}

// JSON 기반 API 요청을 보내고 실패 시 ApiError로 변환해 던지는 공통 요청 함수
export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  opts: { admin?: boolean; adminToken?: string } = {}
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...getHeaders(opts), ...(init.headers as Record<string, string>) },
  })

  if (!res.ok) {
    const body: ApiErrorBody = await res.json().catch(() => ({ error: 'unknown_error' }))
    throw new ApiError(res.status, body)
  }

  return res.json() as Promise<T>
}

// 파일 업로드 등 FormData를 전송하는 POST 요청을 위한 공통 함수
export async function apiRequestForm<T>(
  path: string,
  formData: FormData,
  init: { signal?: AbortSignal } = {}
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: getHeaders({ multipart: true }),
    body: formData,
    signal: init.signal,
  })

  if (!res.ok) {
    const body: ApiErrorBody = await res.json().catch(() => ({ error: 'unknown_error' }))
    throw new ApiError(res.status, body)
  }

  return res.json() as Promise<T>
}

// JSON 요청을 보내되 응답 바디를 Blob으로 받는 공통 함수 (예: TTS 오디오 응답)
export async function apiRequestBlob(path: string, init: RequestInit = {}): Promise<Blob> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...getHeaders(), ...(init.headers as Record<string, string>) },
  })

  if (!res.ok) {
    const body: ApiErrorBody = await res.json().catch(() => ({ error: 'unknown_error' }))
    throw new ApiError(res.status, body)
  }

  return res.blob()
}
