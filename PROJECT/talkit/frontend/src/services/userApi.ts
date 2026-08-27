// 회원가입 및 로그인(세션 생성) 요청을 담당하는 API 서비스
import { apiRequest } from '@/services/apiClient'
import type { SignupRequest, SignupResponse, LoginRequest, LoginResponse } from '@/types/user'

export const userApi = {
  // 신규 사용자 회원가입을 요청
  signup: (body: SignupRequest) =>
    apiRequest<SignupResponse>('/users', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // 로그인 세션을 생성
  login: (body: LoginRequest) =>
    apiRequest<LoginResponse>('/sessions', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
