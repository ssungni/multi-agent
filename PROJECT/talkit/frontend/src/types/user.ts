// 회원가입/로그인 등 사용자 인증 관련 타입 정의
export interface SignupRequest {
  email: string
  name: string
  phone_number: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface UserResponse {
  id: number
  email: string
  name: string
  phone_number: string
}

export interface SignupResponse {
  user: UserResponse
}

export interface LoginResponse {
  user: UserResponse
}
