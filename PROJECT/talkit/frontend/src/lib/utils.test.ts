import { describe, it, expect } from 'vitest'
import { cn, formatCurrency, formatDate, formatDuration, countWords } from './utils'

describe('cn', () => {
  it('여러 클래스명을 공백으로 합친다', () => {
    expect(cn('a', 'b')).toBe('a b')
  })

  it('falsy 값을 무시한다', () => {
    expect(cn('a', false, undefined, null, 'b')).toBe('a b')
  })

  it('충돌하는 tailwind 클래스는 마지막 값이 우선한다', () => {
    expect(cn('px-2', 'px-4')).toBe('px-4')
  })
})

describe('formatCurrency', () => {
  it('KRW는 price_cents를 그대로 원화 금액으로 사용한다', () => {
    expect(formatCurrency(129_000, 'KRW')).toBe('₩129,000')
  })

  it('KRW 0원도 올바르게 표시한다', () => {
    expect(formatCurrency(0, 'KRW')).toBe('₩0')
  })

  it('USD는 cents를 100으로 나눈다', () => {
    // ko-KR 로케일에서는 $와 ₩를 구분하기 위해 USD 기호가 'US$'로 표시된다.
    expect(formatCurrency(150_00, 'USD')).toBe('US$150')
  })
})

describe('formatDate', () => {
  // 정오(UTC) 시각을 사용해 테스트 실행 환경의 타임존에 따라 날짜가
  // 하루 밀리는 것을 방지한다 (±12시간 이내 오프셋에서는 같은 날짜로 유지됨).
  it('ISO 문자열을 한국어 날짜 형식으로 변환한다', () => {
    expect(formatDate('2026-06-20T12:00:00Z')).toBe('2026년 6월 20일')
  })

  it('연/월/일을 모두 포함한다', () => {
    const result = formatDate('2026-01-05T12:00:00Z')
    expect(result).toContain('2026')
    expect(result).toContain('1월')
    expect(result).toContain('5일')
  })
})

describe('formatDuration', () => {
  it('1초 미만이면 n/a를 반환한다', () => {
    expect(formatDuration(500)).toBe('n/a')
    expect(formatDuration(0)).toBe('n/a')
  })

  it('1분 미만이면 "N초"만 표시한다', () => {
    expect(formatDuration(45_000)).toBe('45초')
  })

  it('1분 이상이면 "N분 M초"로 표시한다', () => {
    expect(formatDuration(125_000)).toBe('2분 5초')
  })
})

describe('countWords', () => {
  it('공백으로 구분된 단어 수를 센다', () => {
    expect(countWords('Hello world from me')).toBe(4)
  })

  it('앞뒤 공백과 연속 공백을 무시한다', () => {
    expect(countWords('  Hello   world  ')).toBe(2)
  })

  it('빈 문자열은 0을 반환한다', () => {
    expect(countWords('')).toBe(0)
    expect(countWords('   ')).toBe(0)
  })
})
