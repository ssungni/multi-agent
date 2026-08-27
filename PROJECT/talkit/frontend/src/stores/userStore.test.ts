import { describe, it, expect, beforeEach } from 'vitest'
import { useUserStore } from './userStore'

describe('useUserStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useUserStore.setState({ userId: null, userName: null, adminToken: null })
  })

  it('초기 상태는 userId/userName/adminToken이 모두 null이다', () => {
    const state = useUserStore.getState()
    expect(state.userId).toBeNull()
    expect(state.userName).toBeNull()
    expect(state.adminToken).toBeNull()
  })

  it('setUser는 userId와 userName을 함께 설정한다', () => {
    useUserStore.getState().setUser({ id: 42, name: '홍길동' })
    expect(useUserStore.getState().userId).toBe(42)
    expect(useUserStore.getState().userName).toBe('홍길동')
  })

  it('setAdminToken은 adminToken을 설정한다', () => {
    useUserStore.getState().setAdminToken('secret')
    expect(useUserStore.getState().adminToken).toBe('secret')
  })

  it('clearUser는 userId/userName만 초기화하고 adminToken은 유지한다', () => {
    useUserStore.getState().setUser({ id: 7, name: '홍길동' })
    useUserStore.getState().setAdminToken('secret')

    useUserStore.getState().clearUser()

    expect(useUserStore.getState().userId).toBeNull()
    expect(useUserStore.getState().userName).toBeNull()
    expect(useUserStore.getState().adminToken).toBe('secret')
  })

  it('상태 변경이 localStorage(talkit-user)에 영속화된다', () => {
    useUserStore.getState().setUser({ id: 99, name: '김철수' })

    const raw = localStorage.getItem('talkit-user')
    expect(raw).not.toBeNull()
    const parsed = JSON.parse(raw!)
    expect(parsed.state.userId).toBe(99)
    expect(parsed.state.userName).toBe('김철수')
  })
})
