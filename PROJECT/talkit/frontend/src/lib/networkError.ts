import { ApiError } from '@/services/apiClient'

// fetch()가 서버 응답을 받기 전에 실패하면(네트워크 끊김, DNS 실패 등) TypeError를
// 던진다 — 4xx/5xx 같은 정상 HTTP 에러 응답(ApiError)과 구분해서, 와이파이가 끊긴
// 상황에는 "음성 인식 실패" 대신 정확히 "네트워크 연결 오류"를 보여줄 수 있다.
// 주어진 에러가 네트워크 단절로 인한 fetch 실패인지 판별한다.
export function isNetworkError(err: unknown): boolean {
  return err instanceof TypeError
}

// ApiError(서버가 응답한 에러)면 body.message를 우선 쓰고 없으면 apiErrorFallback을,
// 그 외(네트워크 단절 등)면 networkFallback을 반환한다. 여러 폼/모달에서 반복되던
// "error instanceof ApiError ? (error.body.message ?? ...) : ..." 분기를 통합한다.
export function extractErrorMessage(
  error: unknown,
  apiErrorFallback: string | ((error: ApiError) => string),
  networkFallback: string
): string {
  if (error instanceof ApiError) {
    const fallback =
      typeof apiErrorFallback === 'function' ? apiErrorFallback(error) : apiErrorFallback
    return error.body.message ?? fallback
  }
  return networkFallback
}
