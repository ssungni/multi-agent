// 화면 전반에서 쓰이는 포맷팅/문자열 처리용 공용 유틸 함수 모음.
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// 조건부 클래스명들을 합치고, tailwind 클래스 충돌(예: 동일 속성 중복)을 정리해준다.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(cents: number, currency: string): string {
  // KRW는 소수점 없음 — price_cents가 그대로 원화 금액
  const amount = currency === 'KRW' ? cents : cents / 100
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount)
}

// ISO 날짜 문자열을 "yyyy년 m월 d일" 형태의 한국어 표기로 변환한다.
export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// 대화 완료 화면의 "대화 시간" 표시용 — 1초 미만이면 표시할 의미가 없어 'n/a'를 반환한다.
export function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  if (totalSeconds < 1) return 'n/a'

  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return minutes > 0 ? `${minutes}분 ${seconds}초` : `${seconds}초`
}

// 공백 기준으로 단어 수를 센다 — 연속 공백/앞뒤 공백이 빈 토큰으로 잡히는 것을 막기 위해 filter(Boolean)으로 걸러낸다.
export function countWords(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length
}
