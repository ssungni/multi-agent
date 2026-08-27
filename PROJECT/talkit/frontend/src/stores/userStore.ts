// 로그인한 사용자 정보(아이디/이름)와 관리자 토큰을 보관하는 스토어.
// persist 미들웨어로 localStorage에 저장되어 새로고침 후에도 로그인 상태가 유지된다.
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UserState {
  userId: number | null
  userName: string | null
  adminToken: string | null
  setUser: (user: { id: number; name: string }) => void
  setAdminToken: (token: string) => void
  clearUser: () => void
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      userId: null,
      userName: null,
      adminToken: null,
      // 로그인 성공 시 사용자 식별 정보를 저장
      setUser: ({ id, name }) => set({ userId: id, userName: name }),
      // 관리자 권한 토큰을 별도로 저장 (일반 로그인과 분리 관리)
      setAdminToken: (token) => set({ adminToken: token }),
      // 로그아웃 시 사용자 정보 초기화 (adminToken은 유지됨)
      clearUser: () => set({ userId: null, userName: null }),
    }),
    { name: 'talkit-user' }
  )
)
