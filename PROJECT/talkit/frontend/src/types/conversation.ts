// AI 튜터 대화(연습/실전 모드, 메시지) 관련 타입 정의
export type ConversationStatus =
  | 'idle'
  | 'ai_opening'
  | 'recording'
  | 'vad_processing'
  | 'stt_processing'
  | 'llm_streaming'
  | 'tts_playing'
  | 'error'

// 연습 모드: AI/내 발화 텍스트와 다시 듣기 버튼 모두 보임 (기존 방식).
// 실전 모드: 텍스트/다시 듣기 없이 전화 통화처럼 음성으로만 대화.
export type ConversationMode = 'practice' | 'live'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  // AI 응답은 문장 단위로 나뉘어 TTS가 각각 합성되므로, 한 메시지가 여러 오디오
  // 클립을 가질 수 있다 (다시 듣기 시 순서대로 이어서 재생한다).
  audioUrls?: string[]
  isStreaming?: boolean
}
