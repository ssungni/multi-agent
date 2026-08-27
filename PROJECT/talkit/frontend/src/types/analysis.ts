// 대화 분석 요청/응답 관련 타입 정의
export interface AnalysisRequest {
  messages: Array<{ role: string; content: string }>
}

export interface AnalysisResponse {
  analysis: string
}
