import { describe, it, expect, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useOnlineStatus } from './useOnlineStatus'

describe('useOnlineStatus', () => {
  afterEach(() => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true })
  })

  it('navigator.onLine이 true이면 초기값은 true이다', () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true })
    const { result } = renderHook(() => useOnlineStatus())
    expect(result.current).toBe(true)
  })

  it('navigator.onLine이 false이면 초기값은 false이다', () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true })
    const { result } = renderHook(() => useOnlineStatus())
    expect(result.current).toBe(false)
  })

  it("'offline' 이벤트가 발생하면 false로 바뀐다", () => {
    const { result } = renderHook(() => useOnlineStatus())
    expect(result.current).toBe(true)

    act(() => {
      window.dispatchEvent(new Event('offline'))
    })

    expect(result.current).toBe(false)
  })

  it("'online' 이벤트가 발생하면 다시 true로 바뀐다", () => {
    const { result } = renderHook(() => useOnlineStatus())

    act(() => {
      window.dispatchEvent(new Event('offline'))
    })
    expect(result.current).toBe(false)

    act(() => {
      window.dispatchEvent(new Event('online'))
    })
    expect(result.current).toBe(true)
  })

  it('언마운트 후에는 이벤트 리스너가 더 이상 상태를 바꾸지 않는다', () => {
    const { result, unmount } = renderHook(() => useOnlineStatus())
    unmount()

    act(() => {
      window.dispatchEvent(new Event('offline'))
    })

    // 언마운트되었으므로 마지막으로 읽은 값(true)에서 더 이상 갱신되지 않아야 한다.
    expect(result.current).toBe(true)
  })
})
